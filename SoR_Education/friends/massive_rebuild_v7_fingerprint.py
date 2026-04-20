# massive_rebuild_v7_fingerprint.py
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

def identify_episode(conn, en_list):
    """
    透過內容指紋識別這份字幕真正的 Season/Episode
    """
    cursor = conn.cursor()
    # 抽取 10 句具有特徵的長台詞進行比對
    samples = [en_list[i]['text'] for i in range(len(en_list)//4, len(en_list), len(en_list)//6) if len(en_list[i]['text'].split()) > 6][:5]
    
    votes = {}
    for sample in samples:
        c_sample = clean_text(sample)
        # 在全庫 search_old_backup 中尋找
        cursor.execute('SELECT season, episode FROM scripts_old_backup WHERE line LIKE ?', (f'%{sample[:20]}%',))
        matches = cursor.fetchall()
        for s, e in matches:
            votes[(s, e)] = votes.get((s, e), 0) + 1
            
    if not votes: return None, None
    best_fit = max(votes, key=votes.get)
    return best_fit

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting Fingerprint Rebuild v7.0...")
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
        smi_path = srt_path.replace('.chs.srt', '.en.smi')
        if not os.path.exists(smi_path): continue
        
        ch_list = parse_srt(srt_path)
        en_list = parse_smi(smi_path)
        if not en_list: continue

        # 核心：身分識別
        true_s, true_e = identify_episode(conn, en_list)
        if not true_s:
            print(f"Skipping {os.path.basename(srt_path)} - Identity ambiguous.")
            continue
            
        print(f"Verified: {os.path.basename(srt_path)} is actually Season {true_s} Episode {true_e}")

        # 揉合雙語
        gold_list = []
        ch_ptr = 0
        for en in en_list:
            while ch_ptr < len(ch_list) and ch_list[ch_ptr]['ms'] < en['ms']: ch_ptr += 1
            if ch_ptr < len(ch_list) and abs(ch_list[ch_ptr]['ms'] - en['ms']) < 800:
                gold_list.append({'ms': en['ms'], 'en': en['text'], 'ch': cc.convert(ch_list[ch_ptr]['text'])})
        
        if not gold_list: continue

        # 獲取正確對應集數的 Speaker 參考
        cursor.execute('SELECT line, speaker, action_instruction FROM scripts_old_backup WHERE season=? AND episode=?', (true_s, true_e))
        ref_data = cursor.fetchall()
        ref_dict = {clean_text(r[0]): {'speaker': r[1], 'action': r[2]} for r in ref_data}
        
        # 由於是精確對標，Part 2 自動歸零 (如果檔案名包含 E16-17 或內容是後半集)
        # 這邊簡化邏輯：每份檔案的第一句台詞即為 0
        offset_ms = gold_list[0]['ms']
        
        insert_batch = []
        for sub_idx, sub in enumerate(gold_list):
            c_sub = clean_text(sub['en'])
            ref = ref_dict.get(c_sub, {'speaker': 'Unknown', 'action': ''})
            
            insert_batch.append((
                true_s, true_e, sub_idx, ref['speaker'],
                sub['en'], sub['ch'], ms_to_str(sub['ms'] - offset_ms),
                ref['action'], 80 if ref['speaker'] != "Unknown" else 50
            ))
            
        cursor.executemany('''
            INSERT INTO scripts_rebuild (season, episode, line_index, speaker, line, chinese_line, start_time, action_instruction, priority_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', insert_batch)
        total_added += len(insert_batch)
        conn.commit()

    # 切換資料庫
    cursor.execute('DROP TABLE IF EXISTS scripts;')
    cursor.execute('ALTER TABLE scripts_rebuild RENAME TO scripts;')
    conn.commit()
    conn.close()
    print(f"Fingerprint Rebuild Complete. Total lines: {total_added}")

if __name__ == '__main__':
    main()
