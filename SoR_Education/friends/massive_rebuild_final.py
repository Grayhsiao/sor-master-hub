# massive_rebuild_final.py
import sqlite3
import os
import glob
import re
from opencc import OpenCC

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
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

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
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
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
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
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
    
    print("Starting Ultimate Rebuild (Full Coverage + Zero-Point Correction)...")
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
            theme TEXT,
            tone TEXT,
            action_instruction TEXT,
            literal_translation TEXT,
            priority_score INTEGER DEFAULT 50
        );
    ''')

    total_added = 0

    for season in range(1, 11):
        season_dir = os.path.join(SUB_BASE_DIR, str(season))
        if not os.path.exists(season_dir): continue
        print(f"--- Processing Season {season} ---")
        
        srt_files = sorted(glob.glob(os.path.join(season_dir, '*.srt')))
        for srt_path in srt_files:
            ep_match = re.search(r'S(\d{2})E(\d{2}(?:-\d{2})?)', srt_path, re.IGNORECASE)
            if not ep_match: continue
            
            s_num, e_num_str = int(ep_match.group(1)), ep_match.group(2)
            e_nums = list(range(int(e_num_str.split('-')[0]), int(e_num_str.split('-')[-1])+1)) if '-' in e_num_str else [int(e_num_str)]
            
            ch_list = parse_srt(srt_path)
            en_list = parse_smi(srt_path.replace('.chs.srt', '.en.smi'))
            
            # 揉合雙語為 Gold List
            gold_list = []
            ch_ptr = 0
            for en in en_list:
                while ch_ptr < len(ch_list) and ch_list[ch_ptr]['ms'] < en['ms']: ch_ptr += 1
                if ch_ptr < len(ch_list) and abs(ch_list[ch_ptr]['ms'] - en['ms']) < 800:
                    gold_list.append({'ms': en['ms'], 'en': en['text'], 'ch': cc.convert(ch_list[ch_ptr]['text'])})
            
            if not gold_list: continue

            # 重點：以字幕為循主體，獲取全量覆蓋
            # 為了解決 22 分鐘分集問題，我們需要切割 gold_list
            chunk_size = len(gold_list) // len(e_nums)
            
            for i, e_num in enumerate(e_nums):
                start_i = i * chunk_size
                end_i = (i + 1) * chunk_size if i < len(e_nums) - 1 else len(gold_list)
                current_chunk = gold_list[start_i:end_i]
                
                # 獲取 Speaker 參考資料庫
                cursor.execute('SELECT line, speaker, action_instruction FROM scripts_old_backup WHERE season=? AND episode=?', (s_num, e_num))
                ref_data = cursor.fetchall()
                ref_cleaned = [{'text': clean_text(r[0]), 'speaker': r[1], 'action': r[2]} for r in ref_data]
                
                # 校準偏移量 (讓 Part 2 從 0 開始)
                offset_ms = current_chunk[0]['ms'] if i > 0 else 0
                
                insert_batch = []
                for sub_idx, sub in enumerate(current_chunk):
                    # 嘗試找 Speaker
                    assigned_spk = "Unknown"
                    assigned_act = ""
                    c_sub = clean_text(sub['en'])
                    
                    # 簡單內容匹配
                    for ref in ref_cleaned:
                        if c_sub in ref['text'] or ref['text'] in c_sub:
                            assigned_spk = ref['speaker']
                            assigned_act = ref['action']
                            break
                    
                    insert_batch.append((
                        s_num, e_num, sub_idx, assigned_spk,
                        sub['en'], sub['ch'], ms_to_str(sub['ms'] - offset_ms),
                        assigned_act, 80 if assigned_spk != "Unknown" else 50
                    ))
                
                cursor.executemany('''
                    INSERT INTO scripts_rebuild (season, episode, line_index, speaker, line, chinese_line, start_time, action_instruction, priority_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', insert_batch)
                total_added += len(insert_batch)
        conn.commit()

    cursor.execute('DROP TABLE IF EXISTS scripts;')
    cursor.execute('ALTER TABLE scripts_rebuild RENAME TO scripts;')
    conn.commit()
    conn.close()
    print(f"Ultimate Rebuild Finish. Total lines: {total_added}")

if __name__ == '__main__':
    main()
