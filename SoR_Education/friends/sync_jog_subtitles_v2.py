# sync_jog_subtitles_v2.py
import sqlite3
import os
import glob
import re
import difflib

DB_PATH = 'friends_scripts.db'
SUB_BASE_DIR = '/Users/Gray/Documents/friends/《六人行》(Friends)JOG版本匹配中英文字幕'

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    # 移除標點符號並轉小寫，只保留字母與數字
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text).lower().replace('\n', ' ')
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
    lines_by_time = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) -->', lines[1])
            if time_match:
                t = time_match.group(1)
                text = ' '.join(lines[2:]).strip()
                if text:
                    lines_by_time.append({'time': t, 'text': text})
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
    lines_by_time = []
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
             lines_by_time.append({'time': time_str, 'text': clean})
    return lines_by_time

def main(test_mode=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    total_updated = 0
    
    seasons = range(1, 11) if not test_mode else [1]
    
    for season in seasons:
        season_dir = os.path.join(SUB_BASE_DIR, str(season))
        if not os.path.exists(season_dir): continue
        print(f"Processing Season {season}...")
        
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
            
            # 建立金標雙語 (Gold Reference)
            gold_refs = []
            ch_ptr = 0
            for en_item in en_list:
                # 尋找時間點最接近的中文
                while ch_ptr < len(ch_list) and ch_list[ch_ptr]['time'] < en_item['time']:
                    ch_ptr += 1
                if ch_ptr < len(ch_list) and ch_list[ch_ptr]['time'] == en_item['time']:
                    gold_refs.append({'en': en_item['text'], 'ch': ch_list[ch_ptr]['text'], 'time': en_item['time']})
            
            if not gold_refs: continue
            
            # 對標資料庫
            for e_num in e_nums:
                cursor.execute('SELECT line_index, line FROM scripts WHERE season=? AND episode=? ORDER BY line_index ASC', (s_num, e_num))
                db_lines = cursor.fetchall()
                
                gold_ptr = 0
                updates = []
                
                for db_idx_in_db, db_line_text in db_lines:
                    cleaned_db = clean_text(db_line_text)
                    if not cleaned_db: continue
                    
                    # 在 gold_refs 中用滑動窗口尋找 (當前指標往後看 15 句)
                    best_match_idx = -1
                    best_ratio = 0
                    
                    search_limit = min(gold_ptr + 15, len(gold_refs))
                    for i in range(gold_ptr, search_limit):
                        cleaned_gold_en = clean_text(gold_refs[i]['en'])
                        # 包含匹配或高比例模糊匹配
                        if cleaned_db in cleaned_gold_en or cleaned_gold_en in cleaned_db:
                            best_match_idx = i
                            break
                        
                        ratio = difflib.SequenceMatcher(None, cleaned_db, cleaned_gold_en).ratio()
                        if ratio > 0.85:
                            best_match_idx = i
                            break
                    
                    if best_match_idx != -1:
                        match = gold_refs[best_match_idx]
                        t_fixed = match['time'].replace(',', '.')
                        updates.append((match['ch'], t_fixed, s_num, e_num, db_idx_in_db))
                        # 更新指針，防止倒退
                        gold_ptr = best_match_idx + 1
                
                for upd in updates:
                    cursor.execute('UPDATE scripts SET chinese_line = ?, start_time = ? WHERE season=? AND episode=? AND line_index=?', upd)
                total_updated += len(updates)
                if test_mode and updates: print(f"Test Ep {e_num}: Matched {len(updates)} lines.")

        conn.commit()
    conn.close()
    print(f"Sync Complete. Total Updated: {total_updated}")

if __name__ == '__main__':
    import sys
    test = '--test' in sys.argv
    main(test_mode=test)
