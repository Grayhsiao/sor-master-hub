# massive_rebuild.py
import sqlite3
import os
import glob
import re
import difflib

# 路徑定義
DB_PATH = 'friends_scripts.db'
SUB_BASE_DIR = '/Users/Gray/Documents/friends/《六人行》(Friends)JOG版本匹配中英文字幕'

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
    return ' '.join(text.split())

def time_to_ms(time_str):
    """將 00:00:00,000 轉換為毫秒"""
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

def ms_to_str(ms):
    """將毫秒轉換為 00:00:00.000"""
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
                t_str = time_match.group(1)
                text = ' '.join(lines[2:]).strip()
                if text: items.append({'time_ms': time_to_ms(t_str), 'text': text})
    return items

def parse_smi(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
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
        clean = re.sub(r'&nbsp;', ' ', clean).strip()
        clean = clean.replace('\r', '').replace('\n', ' ').strip()
        if clean: items.append({'time_ms': int(ms_time), 'text': clean})
    return items

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Initializing precise database structure (v4.0 Correction)...")
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
            priority_score INTEGER DEFAULT 50
        );
    ''')

    total_blocks_added = 0

    for season in range(1, 11):
        season_dir = os.path.join(SUB_BASE_DIR, str(season))
        if not os.path.exists(season_dir): continue
        print(f"--- Rebuilding Season {season} ---")
        
        srt_files = sorted(glob.glob(os.path.join(season_dir, '*.srt')))
        for srt_path in srt_files:
            ep_match = re.search(r'S(\d{2})E(\d{2}(?:-\d{2})?)', srt_path, re.IGNORECASE)
            if not ep_match: continue
            
            s_num = int(ep_match.group(1))
            e_num_str = ep_match.group(2)
            e_nums = list(range(int(e_num_str.split('-')[0]), int(e_num_str.split('-')[-1])+1)) if '-' in e_num_str else [int(e_num_str)]
            
            smi_path = srt_path.replace('.chs.srt', '.en.smi')
            if not os.path.exists(smi_path): continue
            
            ch_list = parse_srt(srt_path)
            en_list = parse_smi(smi_path)
            
            # 揉合雙語，對準時間
            gold_subs = []
            ch_ptr = 0
            for en_item in en_list:
                while ch_ptr < len(ch_list) and ch_list[ch_ptr]['time_ms'] < en_item['time_ms']:
                    ch_ptr += 1
                if ch_ptr < len(ch_list) and abs(ch_list[ch_ptr]['time_ms'] - en_item['time_ms']) < 500:
                    gold_subs.append({'en': en_item['text'], 'ch': ch_list[ch_ptr]['text'], 'ms': en_item['time_ms']})
            
            if not gold_subs: continue

            # 重點：指針在處理「多集檔案」時不歸零
            gold_ptr = 0
            
            for episode_idx_in_file, e_num in enumerate(e_nums):
                # 從舊備份中獲取 Speaker 資訊 (為了嫁接)
                cursor.execute('SELECT line, speaker, action_instruction, theme, tone FROM scripts_old_backup WHERE season=? AND episode=? ORDER BY line_index ASC', (s_num, e_num))
                old_data = cursor.fetchall()
                
                results_to_insert = []
                episode_start_ms = -1 # 這一集在檔案中的起始毫秒
                
                for db_idx, old_row in enumerate(old_data):
                    old_line_text, old_speaker, old_action, old_theme, old_tone = old_row
                    cleaned_db = clean_text(old_line_text)
                    if not cleaned_db: continue
                    
                    found_sub = None
                    search_limit = min(gold_ptr + 15, len(gold_subs))
                    for i in range(gold_ptr, search_limit):
                        cleaned_gold = clean_text(gold_subs[i]['en'])
                        if cleaned_db in cleaned_gold or cleaned_gold in cleaned_db or difflib.SequenceMatcher(None, cleaned_db, cleaned_gold).ratio() > 0.8:
                            found_sub = gold_subs[i]
                            gold_ptr = i + 1
                            break
                    
                    if found_sub:
                        # 零點校準邏輯
                        if episode_start_ms == -1:
                            episode_start_ms = found_sub['ms']
                        
                        relative_ms = found_sub['ms'] - episode_start_ms
                        results_to_insert.append((
                            s_num, e_num, db_idx,
                            old_speaker, found_sub['en'], found_sub['ch'],
                            ms_to_str(relative_ms),
                            old_theme, old_tone, old_action,
                            80 if old_speaker != 'Unknown' else 50
                        ))

                if results_to_insert:
                    cursor.executemany('''
                        INSERT INTO scripts_rebuild (season, episode, line_index, speaker, line, chinese_line, start_time, theme, tone, action_instruction, priority_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', results_to_insert)
                    total_blocks_added += len(results_to_insert)
            
        conn.commit()
    
    # 簡轉繁 (順便在這裡做，避免多跑一次)
    from opencc import OpenCC
    cc = OpenCC('s2t')
    print("Converting to Traditional Chinese...")
    cursor.execute('UPDATE scripts_rebuild SET chinese_line = chinese_line') # dummy
    cursor.execute('SELECT id, chinese_line FROM scripts_rebuild')
    to_convert = cursor.fetchall()
    updates = [(cc.convert(ch), rid) for rid, ch in to_convert if ch]
    cursor.executemany('UPDATE scripts_rebuild SET chinese_line = ? WHERE id = ?', updates)
    conn.commit()

    # 切換
    cursor.execute('DROP TABLE IF EXISTS scripts;')
    cursor.execute('ALTER TABLE scripts_rebuild RENAME TO scripts;')
    conn.commit()
    conn.close()
    print(f"Time Correction Rebuild Complete! Total blocks: {total_blocks_added}")

if __name__ == '__main__':
    main()
