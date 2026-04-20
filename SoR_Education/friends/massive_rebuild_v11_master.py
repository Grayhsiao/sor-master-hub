# massive_rebuild_v11_master.py
import sqlite3
import os
import glob
import re
from opencc import OpenCC
import difflib

# 數據路徑
DB_PATH = 'friends_scripts.db'
SUB_BASE_DIR = '/Users/Gray/Documents/friends/《六人行》(Friends)JOG版本匹配中英文字幕'
cc = OpenCC('s2t')

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    return ' '.join(text.split())

def time_to_ms(t_str):
    if ':' not in t_str: return 0
    parts = t_str.split(':')
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
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f: content = f.read()
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
            with open(filepath, 'r', encoding=enc, errors='replace') as f: content = f.read()
            break
        except Exception: pass
    matches = re.finditer(r'<SYNC Start=(\d+)><P Class=ENCC(?:&nbsp;)?>(.*?)(?=<SYNC|</BODY>|<\!--)', content, re.DOTALL | re.IGNORECASE)
    items = []
    for m in matches:
        ms_time = int(m.group(1))
        text = re.sub(r'<[^>]+>', ' ', m.group(2)).strip().replace('\n', ' ')
        if text and text != '&nbsp;':
            items.append({'ms': ms_time, 'text': text})
    return items

def identify_episode_content(conn, sn_hint, en_list):
    """
    透過英文對白在該季中精確辨識集數
    """
    cursor = conn.cursor()
    samples = [e['text'] for e in en_list if len(e['text'].split()) > 8][:10]
    votes = {}
    for sample in samples:
        cursor.execute("SELECT episode FROM scripts_old_backup WHERE season=? AND line LIKE ?", (sn_hint, f'%{sample[:30]}%'))
        for (ep,) in cursor.fetchall():
            votes[ep] = votes.get(ep, 0) + 1
    if not votes: return None
    return max(votes, key=votes.get)

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Initializing Master Synthesis v11.0 (Bilingual Bridge Mode)...")
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

    for sn in range(1, 11):
        season_dir = os.path.join(SUB_BASE_DIR, str(sn))
        srt_files = sorted(glob.glob(os.path.join(season_dir, "*.chs.srt")))
        
        # 獲取本季所有劇本作為參考
        cursor.execute("SELECT line, speaker, action_instruction, episode, line_index FROM scripts_old_backup WHERE season=? ORDER BY episode, line_index", (sn,))
        season_ref = cursor.fetchall()
        # 建立全局 Season 字典以便跨集匹配
        season_dict = {}
        for r in season_ref:
            c = clean_text(r[0])
            if c not in season_dict: season_dict[c] = []
            season_dict[c].append({'spk': r[1], 'act': r[2], 'ep': r[3], 'idx': r[4]})

        for srt_path in srt_files:
            smi_path = srt_path.replace('.chs.srt', '.en.smi')
            ch_list = parse_srt(srt_path)
            en_list = parse_smi(smi_path) if os.path.exists(smi_path) else []
            
            if not ch_list: continue
            
            # 1. 識別此檔案真正的身分 (首選內容對標)
            true_e = identify_episode_content(conn, sn, en_list) if en_list else None
            if not true_e:
                # 降級從檔名獲取
                m = re.search(r'E(\d{2})', os.path.basename(srt_path))
                true_e = int(m.group(1)) if m else 1
            
            print(f"Processing: Season {sn} Ep {true_e} <- {os.path.basename(srt_path)}")

            # 2. 以中文 SRT 為主軸進行編織
            insert_batch = []
            ep_start_ms = ch_list[0]['ms']
            current_ep = true_e
            
            for idx, ch in enumerate(ch_list):
                # 尋找對應的英文 JOG 字幕
                en_match = next((e for e in en_list if abs(e['ms'] - ch['ms']) < 1200), None)
                en_text = en_match['text'] if en_match else ""
                
                # 尋找對應的角色與劇本資訊 (Grafting)
                # 如果 JOG 有英文，優先拿 JOG 英文去對標；否則跳過名字 (Unknown)
                assigned_spk = "Unknown"
                assigned_act = ""
                
                if en_text:
                    c_en = clean_text(en_text)
                    if c_en in season_dict:
                        ref = season_dict[c_en][0] # 取第一個匹配
                        assigned_spk = ref['spk']
                        assigned_act = ref['act']
                        # 偵測集數切換 (Zero-Point Reset for multi-ep files)
                        if ref['ep'] != current_ep:
                            current_ep = ref['ep']
                            ep_start_ms = ch['ms']
                
                insert_batch.append((
                    sn, current_ep, idx, assigned_spk,
                    en_text or "[Extended Line]", cc.convert(ch['text']),
                    ms_to_str(ch['ms'] - ep_start_ms),
                    assigned_act
                ))
            
            if insert_batch:
                cursor.executemany('''
                    INSERT INTO scripts_rebuild (season, episode, line_index, speaker, line, chinese_line, start_time, action_instruction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', insert_batch)
                conn.commit()

    cursor.execute('DROP TABLE IF EXISTS scripts;')
    cursor.execute('ALTER TABLE scripts_rebuild RENAME TO scripts;')
    conn.commit()
    conn.close()
    print("Master Synthesis v11.0 Finished.")

if __name__ == '__main__':
    main()
