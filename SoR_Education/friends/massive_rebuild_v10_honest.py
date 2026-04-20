# massive_rebuild_v10_honest.py
import sqlite3
import os
import glob
import re
from opencc import OpenCC
import difflib

# 數據源路徑
DB_PATH = 'friends_scripts.db'
SUB_BASE_DIR = '/Users/Gray/Documents/friends/《六人行》(Friends)JOG版本匹配中英文字幕'
cc = OpenCC('s2t')

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    return ' '.join(text.split())

def ms_to_str(ms):
    if ms < 0: ms = 0
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    # 使用 . 為毫秒分隔符以符合搜尋習慣
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:03d}'

def time_to_ms(t_str):
    if ':' not in t_str: return 0
    parts = t_str.split(':')
    h, m, s_ms = parts
    s, ms = s_ms.split(',') if ',' in s_ms else (s_ms, '000')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

def parse_srt(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
            break
        except Exception: pass
    blocks = re.split(r'\n\s*\n', content)
    items = []
    for b in blocks:
        lines = b.strip().split('\n')
        if len(lines) >= 3:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) -->', lines[1])
            if time_match:
                items.append({'ms': time_to_ms(time_match.group(1)), 'text': ' '.join(lines[2:]).strip()})
    return items

def parse_smi(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
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
        if clean: items.append({'ms': int(ms_time), 'text': clean.replace('\n', ' ')})
    return items

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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

    all_srt = []
    for s in range(1, 11):
        all_srt.extend(glob.glob(os.path.join(SUB_BASE_DIR, str(s), '*.srt')))
    
    total_added = 0
    
    for srt_path in sorted(all_srt):
        m = re.search(r'S(\d{2})E(\d{2}(?:-\d{2})?)', srt_path, re.IGNORECASE)
        if not m: continue
        
        s_num = int(m.group(1))
        e_nums = list(range(int(m.group(2).split('-')[0]), int(m.group(2).split('-')[-1])+1)) if '-' in m.group(2) else [int(m.group(2))]
        
        smi_path = srt_path.replace('.chs.srt', '.en.smi')
        if not os.path.exists(smi_path): continue
        
        ch_list = parse_srt(srt_path)
        en_list = parse_smi(smi_path)
        if not en_list: continue

        # 融合雙語
        gold_list = []
        ch_ptr = 0
        for en in en_list:
            while ch_ptr < len(ch_list) and ch_list[ch_ptr]['ms'] < en['ms']: ch_ptr += 1
            if ch_ptr < len(ch_list) and abs(ch_list[ch_ptr]['ms'] - en['ms']) < 1000:
                gold_list.append({'ms': en['ms'], 'en': en['text'], 'ch': cc.convert(ch_list[ch_ptr]['text'])})
        
        if not gold_list: continue

        gold_ptr = 0
        for e_num in e_nums:
            # 獲取本集模板
            cursor.execute('SELECT line, speaker, action_instruction, line_index FROM scripts_old_backup WHERE season=? AND episode=? ORDER BY line_index ASC', (s_num, e_num))
            ref_data = cursor.fetchall()
            
            # --- 優化點：建立字典索引 ---
            ref_map = {}
            ref_list = []
            for r in ref_data:
                cleaned = clean_text(r[0])
                info = {'speaker': r[1], 'action': r[2], 'idx': r[3]}
                ref_map[cleaned] = info
                ref_list.append({'text': cleaned, **info})

            insert_batch = []
            ep_start_ms = gold_list[gold_ptr]['ms'] if gold_ptr < len(gold_list) else 0

            if len(e_nums) == 1:
                # 單集模式：O(1) 字典優先，找不到才 O(N) 模糊匹配
                for sub_idx, sub in enumerate(gold_list):
                    c_sub = clean_text(sub['en'])
                    ref = ref_map.get(c_sub)
                    assigned_spk, assigned_act = "Unknown", ""
                    if ref:
                        assigned_spk, assigned_act = ref['speaker'], ref['action']
                    else:
                        # 局部窗口模糊比對 (優化：只找附近)
                        for r_item in ref_list:
                            if c_sub in r_item['text'] or r_item['text'] in c_sub or difflib.SequenceMatcher(None, c_sub, r_item['text']).ratio() > 0.8:
                                assigned_spk, assigned_act = r_item['speaker'], r_item['action']
                                break
                    
                    insert_batch.append((
                        s_num, e_num, sub_idx, assigned_spk,
                        sub['en'], sub['ch'], ms_to_str(sub['ms'] - ep_start_ms),
                        assigned_act, 80 if assigned_spk != 'Unknown' else 50
                    ))
            else:
                # 多集模式 (E16-17)：維持流動指針
                for r_item in ref_list:
                    found = None
                    limit = min(gold_ptr + 20, len(gold_list))
                    for i in range(gold_ptr, limit):
                        c_gold = clean_text(gold_list[i]['en'])
                        if r_item['text'] in c_gold or c_gold in r_item['text'] or difflib.SequenceMatcher(None, r_item['text'], c_gold).ratio() > 0.8:
                            found = gold_list[i]
                            gold_ptr = i + 1
                            break
                    if found:
                        insert_batch.append((
                            s_num, e_num, r_item['idx'], r_item['speaker'],
                            found['en'], found['ch'], ms_to_str(found['ms'] - ep_start_ms),
                            r_item['action'], 80 if r_item['speaker'] != 'Unknown' else 50
                        ))
            
            if insert_batch:
                cursor.executemany('''
                    INSERT INTO scripts_rebuild (season, episode, line_index, speaker, line, chinese_line, start_time, action_instruction, priority_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', insert_batch)
                total_added += len(insert_batch)
        
        print(f"Layed down: S{s_num:02d} - {os.path.basename(srt_path)}")
        conn.commit()

    cursor.execute('DROP TABLE IF EXISTS scripts;')
    cursor.execute('ALTER TABLE scripts_rebuild RENAME TO scripts;')
    conn.commit()
    conn.close()
    print(f"Fast Rebuild v10.0 optimized Complete. Total lines: {total_added}")

if __name__ == '__main__':
    main()
