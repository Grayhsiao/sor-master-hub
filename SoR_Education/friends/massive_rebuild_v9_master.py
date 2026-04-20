# massive_rebuild_v9_master.py
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

def time_to_ms(time_str):
    if ':' not in time_str: return 0
    parts = time_str.split(':')
    h, m, s_ms = parts
    s, ms = s_ms.split(',') if ',' in s_ms else (s_ms, '000')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

def ms_to_str(ms):
    if ms < 0: ms = 0
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:03d}'

def parse_srt(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
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
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
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
        clean = clean.replace('\n', ' ').strip()
        if clean: items.append({'ms': int(ms_time), 'text': clean})
    return items

def identify_episode(conn, en_list):
    cursor = conn.cursor()
    # 抽取 10 句具有特徵的長台詞進行身分比對
    candidate_samples = [e['text'] for e in en_list if len(e['text'].split()) > 8]
    if not candidate_samples: return None, None
    
    samples = [candidate_samples[i] for i in range(0, len(candidate_samples), len(candidate_samples)//5 + 1)][:10]
    votes = {}
    for sample in samples:
        cursor.execute('SELECT season, episode FROM scripts_old_backup WHERE line LIKE ?', (f'%{sample[:30]}%',))
        for s, e in cursor.fetchall():
            votes[(s, e)] = votes.get((s, e), 0) + 1
            
    if not votes: return None, None
    return max(votes, key=votes.get)

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Initializing Mastery Rebuild v9.0 (Subtitle Skeleton Mode)...")
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
        smi_path = srt_path.replace('.chs.srt', '.en.smi')
        if not os.path.exists(smi_path): continue
        
        ch_list = parse_srt(srt_path)
        en_list = parse_smi(smi_path)
        if not en_list: continue

        # A. 識別真實身分
        true_s, true_e = identify_episode(conn, en_list)
        if not true_s:
            # 如果比對失敗，降級從檔名猜測 (這是為了保留 copy boy 這種劇本漏掉的集數)
            m = re.search(r'S(\d{2})E(\d{2}(?:-\d{2})?)', srt_path, re.IGNORECASE)
            if not m: continue
            true_s = int(m.group(1))
            true_e_str = m.group(2)
            true_e = int(true_e_str.split('-')[0]) # 先取第一集
        
        print(f"Assigning: {os.path.basename(srt_path)} -> Season {true_s} Episode {true_e}")

        # B. 雙語融合
        gold_list = []
        ch_ptr = 0
        for en in en_list:
            while ch_ptr < len(ch_list) and ch_list[ch_ptr]['ms'] < en['ms']: ch_ptr += 1
            if ch_ptr < len(ch_list) and abs(ch_list[ch_ptr]['ms'] - en['ms']) < 1000:
                gold_list.append({'ms': en['ms'], 'en': en['text'], 'ch': cc.convert(ch_list[ch_ptr]['text'])})
        
        if not gold_list: continue

        # C. 分割連播集並賦予姓名 (Grafting)
        # 先獲取該季全劇本作為特徵庫
        cursor.execute('SELECT line, speaker, action_instruction, episode FROM scripts_old_backup WHERE season=?', (true_s,))
        master_ref = cursor.fetchall()
        master_dict = {clean_text(r[0]): {'speaker': r[1], 'action': r[2], 'ep': r[3]} for r in master_ref}

        insert_batch = []
        episode_start_ms = gold_list[0]['ms']
        last_found_ep = true_e
        
        for idx, sub in enumerate(gold_list):
            c_sub = clean_text(sub['en'])
            ref_info = master_dict.get(c_sub, {'speaker': 'Unknown', 'action': '', 'ep': last_found_ep})
            
            # 偵測集數切換 (Zero-Point Reset)
            if ref_info['ep'] != last_found_ep:
                episode_start_ms = sub['ms']
                last_found_ep = ref_info['ep']
            
            insert_batch.append((
                true_s, last_found_ep, idx, ref_info['speaker'],
                sub['en'], sub['ch'], ms_to_str(sub['ms'] - episode_start_ms),
                ref_info['action'], 80 if ref_info['speaker'] != 'Unknown' else 50
            ))

        if insert_batch:
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
    print(f"Mastery Rebuild v9.0 Finish. Total lines: {total_added}")

if __name__ == '__main__':
    main()
