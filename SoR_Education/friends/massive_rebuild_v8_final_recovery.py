# massive_rebuild_v8_final_recovery.py
import sqlite3
import os
import glob
import re
from opencc import OpenCC
import difflib

# 路徑與工具
DB_PATH = 'friends_scripts.db'
SUB_BASE_DIR = '/Users/Gray/Documents/friends/《六人行》(Friends)JOG版本匹配中英文字幕'
cc = OpenCC('s2t')

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
    return ' '.join(text.split())

def time_to_ms(time_str):
    if ':' not in time_str: return 0
    parts = time_str.split(':')
    if len(parts) == 3:
        h, m, s_ms = parts
        s, ms = s_ms.split(',') if ',' in s_ms else (s_ms, '000')
        return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)
    return 0

def ms_to_str(ms):
    if ms < 0: ms = 0
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:03d}'

def parse_srt(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030']
    content = ""
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f: content = f.read()
            break
        except Exception: pass
    blocks = re.split(r'\n\s*\n', content)
    items = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) -->', lines[1])
            if time_match:
                items.append({'ms': time_to_ms(time_match.group(1)), 'text': ' '.join(lines[2:]).strip()})
    return items

def parse_smi(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030']
    content = ""
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f: content = f.read()
            break
        except Exception: pass
    matches = re.findall(r'<SYNC Start=(\d+)><P Class=ENCC(?:&nbsp;)?>(.*?)(?=<SYNC|</BODY>|<\!--)', content, re.DOTALL | re.IGNORECASE)
    items = []
    for ms_time, text in matches:
        clean = re.sub(r'<[^>]+>', ' ', text).strip()
        clean = re.sub(r'&nbsp;', ' ', clean).strip().replace('\n', ' ')
        if clean: items.append({'ms': int(ms_time), 'text': clean})
    return items

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting Final Recovery Rebuild v8.0...")
    cursor.execute('DROP TABLE IF EXISTS scripts_rebuild;')
    cursor.execute('''
        CREATE TABLE scripts_rebuild (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season INTEGER,
            episode INTEGER,
            line_index INTEGER,
            speaker TEXT,
            line TEXT,
            chinese_line TEXT,
            start_time TEXT,
            action_instruction TEXT,
            literal_translation TEXT,
            priority_score INTEGER DEFAULT 50
        );
    ''')

    # 獲取所有字幕檔案
    all_srt = []
    for s in range(1, 11):
        all_srt.extend(glob.glob(os.path.join(SUB_BASE_DIR, str(s), '*.srt')))
    
    total_added = 0

    for srt_path in sorted(all_srt):
        # 1. 解析檔案名作為初步建議
        ep_match = re.search(r'S(\d{2})E(\d{2}(?:-\d{2})?)', srt_path, re.IGNORECASE)
        suggested_s = int(ep_match.group(1)) if ep_match else 1
        suggested_e_str = ep_match.group(2) if ep_match else "1"
        suggested_e_list = list(range(int(suggested_e_str.split('-')[0]), int(suggested_e_str.split('-')[-1])+1)) if '-' in suggested_e_str else [int(suggested_e_str)]

        smi_path = srt_path.replace('.chs.srt', '.en.smi')
        if not os.path.exists(smi_path): continue
        
        ch_list = parse_srt(srt_path)
        en_list = parse_smi(smi_path)
        if not en_list: continue

        # 2. 揉合雙語為 Gold List
        gold_list = []
        ch_ptr = 0
        for en in en_list:
            while ch_ptr < len(ch_list) and ch_list[ch_ptr]['ms'] < en['ms']: ch_ptr += 1
            if ch_ptr < len(ch_list) and abs(ch_list[ch_ptr]['ms'] - en['ms']) < 800:
                gold_list.append({'ms': en['ms'], 'en': en['text'], 'ch': cc.convert(ch_list[ch_ptr]['text'])})
        
        if not gold_list: continue

        # 3. 智能分配集數 (不均分，改用台詞匹配來找邊界)
        gold_ptr = 0
        for e_num in suggested_e_list:
            # 獲取該集 Speaker 參考
            cursor.execute('SELECT line, speaker, action_instruction, line_index FROM scripts_old_backup WHERE season=? AND episode=? ORDER BY line_index ASC', (suggested_s, e_num))
            ref_data = cursor.fetchall()
            
            ref_list = [{'text': clean_text(r[0]), 'speaker': r[1], 'action': r[2], 'idx': r[3]} for r in ref_data]
            if not ref_list: continue

            insert_batch = []
            episode_start_ms = -1
            
            # 使用滑動窗口匹配，確保內容對標
            for ref in ref_list:
                found_match = None
                search_range = min(gold_ptr + 10, len(gold_list))
                for i in range(gold_ptr, search_range):
                    c_gold = clean_text(gold_list[i]['en'])
                    if ref['text'] in c_gold or c_gold in ref['text'] or difflib.SequenceMatcher(None, ref['text'], c_gold).ratio() > 0.8:
                        found_match = gold_list[i]
                        gold_ptr = i + 1
                        break
                
                if found_match:
                    if episode_start_ms == -1: episode_start_ms = found_match['ms']
                    
                    insert_batch.append((
                        suggested_s, e_num, ref['idx'], ref['speaker'],
                        found_match['en'], found_match['ch'], ms_to_str(found_match['ms'] - episode_start_ms),
                        ref['action'], 80 if ref['speaker'] != "Unknown" else 50
                    ))

            if insert_batch:
                cursor.executemany('''
                    INSERT INTO scripts_rebuild (season, episode, line_index, speaker, line, chinese_line, start_time, action_instruction, priority_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', insert_batch)
                total_added += len(insert_batch)
                print(f"Ingested {len(insert_batch)} lines into S{suggested_s:02d}E{e_num:02d}")

        conn.commit()

    # 切換資料庫
    cursor.execute('DROP TABLE IF EXISTS scripts;')
    cursor.execute('ALTER TABLE scripts_rebuild RENAME TO scripts;')
    conn.commit()
    conn.close()
    print(f"Final Recovery v8.0 Finish. Total lines: {total_added}")

if __name__ == '__main__':
    main()
