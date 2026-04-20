# speaker_recovery.py
import sqlite3
import difflib
import re

def clean(t):
    if not t: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', t).lower()

conn = sqlite3.connect('friends_scripts.db')
cursor = conn.cursor()

# 獲取所有 Unknown 的行
cursor.execute("SELECT id, season, episode, line FROM scripts WHERE speaker = 'Unknown'")
unknowns = cursor.fetchall()

print(f"Total Unknown lines to recover: {len(unknowns)}")

# 預先加載舊劇本緩存，提高速度
old_cache = {}

for uid, s, e, line in unknowns:
    cleaned_line = clean(line)
    if not cleaned_line: continue
    
    # 緩存機制
    cache_key = (s, e)
    if cache_key not in old_cache:
        cursor.execute("SELECT speaker, line FROM scripts_old_backup WHERE season=? AND episode=?", (s, e))
        old_cache[cache_key] = cursor.fetchall()
    
    candidates = old_cache[cache_key]
    best_speaker = None
    best_ratio = 0
    
    for spk, old_line in candidates:
        cleaned_old = clean(old_line)
        # 包含關係在字幕斷句中非常常見
        if cleaned_line in cleaned_old or cleaned_old in cleaned_line:
            best_speaker = spk
            best_ratio = 1.0
            break
        
        # 模糊比對
        ratio = difflib.SequenceMatcher(None, cleaned_line, cleaned_old).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_speaker = spk
            
    if best_speaker and (best_ratio > 0.6):
        cursor.execute("UPDATE scripts SET speaker = ? WHERE id = ?", (best_speaker, uid))

conn.commit()
print("Speaker recovery complete.")
conn.close()
