# sync_jog_subtitles.py
import sqlite3
import os
import glob
import re
import difflib

DB_PATH = 'friends_scripts.db'
SUB_BASE_DIR = '/Users/Gray/Documents/friends/《六人行》(Friends)JOG版本匹配中英文字幕'

def clean_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'[^\w\s]', '', text).lower().replace('\n', ' ')
    return ' '.join(text.split())

def parse_srt(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
    content = ""
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
            break
        except Exception:
            pass
            
    blocks = re.split(r'\n\s*\n', content)
    lines_by_time = {}
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) -->', lines[1])
            if time_match:
                t = time_match.group(1)
                text = ' '.join(lines[2:]).strip()
                if text:
                    lines_by_time[t] = text
    return lines_by_time

def parse_smi(filepath):
    encodings = ['gbk', 'utf-8', 'gb18030', 'utf-16']
    content = ""
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
            break
        except Exception:
            pass
            
    matches = re.findall(r'<SYNC Start=(\d+)><P Class=ENCC(?:&nbsp;)?>(.*?)(?=<SYNC|</BODY>|<\!--)', content, re.DOTALL | re.IGNORECASE)
    lines_by_time = {}
    for ms_time, text in matches:
        ms = int(ms_time)
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        time_str = f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
        clean = re.sub(r'<[^>]+>', ' ', text).strip()
        clean = re.sub(r'&nbsp;', ' ', clean).strip()
        clean = clean.replace('\r', '').replace('\n', ' ').strip()
        if clean:
             lines_by_time[time_str] = clean
    return lines_by_time

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_updated = 0
    
    for season in range(1, 11):
        season_dir = os.path.join(SUB_BASE_DIR, str(season))
        if not os.path.exists(season_dir):
            continue
            
        print(f"Processing Season {season}...")
        
        # episodes are separated by files. 
        # file names are like: [六人行].Friends.S01E01.The.One...
        srt_files = glob.glob(os.path.join(season_dir, '*.srt'))
        for srt_path in srt_files:
            ep_match = re.search(r'S(\d{2})E(\d{2}(?:-\d{2})?)', srt_path, re.IGNORECASE)
            if not ep_match:
                continue
            
            s_num = int(ep_match.group(1))
            e_num_str = ep_match.group(2)
            # handle double episodes like S01E16-17
            e_nums = []
            if '-' in e_num_str:
                e1, e2 = map(int, e_num_str.split('-'))
                e_nums.extend(range(e1, e2+1))
            else:
                e_nums.append(int(e_num_str))
                
            smi_path = srt_path.replace('.chs.srt', '.en.smi')
            if not os.path.exists(smi_path):
                continue
                
            ch_data = parse_srt(srt_path)
            en_data = parse_smi(smi_path)
            
            # map time to en and ch
            matched_pairs = []
            for t, en_text in en_data.items():
                if t in ch_data: # exact match
                    matched_pairs.append({
                        'time': t,
                        'en': en_text,
                        'ch': ch_data[t]
                    })
                    
            if not matched_pairs:
                continue
                
            # fetch db lines for this episode
            for e_num in e_nums:
                cursor.execute('SELECT line_index, line, chinese_line FROM scripts WHERE season=? AND episode=?', (s_num, e_num))
                db_lines = cursor.fetchall()  # (index, text, chinese_line)
                
                updates = []
                for db_idx, db_line_text, db_chinese in db_lines:
                    if db_chinese: # already has good translation
                        continue
                    
                    cleaned_db = clean_text(db_line_text)
                    if not cleaned_db:
                        continue
                        
                    # find best match in matched_pairs
                    best_match = None
                    best_ratio = 0
                    
                    for pair in matched_pairs:
                        cleaned_pair_en = clean_text(pair['en'])
                        # checks if the DB line is heavily present in the subtitle EN line or vice versa
                        if cleaned_db in cleaned_pair_en or cleaned_pair_en in cleaned_db:
                            best_match = pair
                            break
                        
                        ratio = difflib.SequenceMatcher(None, cleaned_db, cleaned_pair_en).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = pair
                    
                    # Update if a strong match is found
                    if best_match and (best_ratio > 0.8 or cleaned_db in clean_text(best_match['en'])):
                        # format time string
                        t = best_match['time']
                        start_time = t.replace(',', '.')
                        
                        updates.append((best_match['ch'], start_time, s_num, e_num, db_idx))
                
                # execute batch updates for this episode
                for upd in updates:
                    cursor.execute('''
                        UPDATE scripts SET chinese_line = ?, start_time = ? 
                        WHERE season=? AND episode=? AND line_index=?
                    ''', upd)
                
                total_updated += len(updates)
                
        # commit per season
        conn.commit()
        print(f"Season {season} complete. Updated so far: {total_updated}")

    print(f"Total lines updated: {total_updated}")
    conn.close()

if __name__ == '__main__':
    main()
