import sqlite3
import re

def calculate_score(line, speaker, chinese_line):
    score = 0
    words = line.split()
    word_count = len(words)

    # 1. 經典金句關鍵字 (至高無上權重)
    gold_keywords = {
        'pivot': 100, 
        'lobster': 100, 
        'unagi': 100, 
        'seven': 80, 
        'break': 90, 
        'sandwich': 80, 
        'smelly cat': 100,
        'moo point': 90,
        'transponster': 90,
        'plane': 70
    }
    
    line_lower = line.lower()
    for kw, bonus in gold_keywords.items():
        if kw in line_lower:
            score += bonus

    # 2. 教學黃金長度 (8-20 個單字最適合教學)
    if 8 <= word_count <= 20:
        score += 20
    elif 4 <= word_count < 8:
        score += 10
    
    # 3. 翻譯完備度 (已有翻譯的優先顯示)
    if chinese_line and '處理中' not in chinese_line:
        score += 15

    # 4. 角色標誌性情緒 (例如 Chandler 的 sarcasm)
    if speaker == 'Chandler' and '?' in line:
        score += 5
    if speaker == 'Ross' and '!' in line:
        score += 5
        
    return score

def main():
    conn = sqlite3.connect('friends_scripts.db')
    cursor = conn.cursor()
    
    print("Reading all scripts...")
    cursor.execute("SELECT rowid, line, speaker, chinese_line FROM scripts")
    rows = cursor.fetchall()
    
    updates = []
    print(f"Scoring {len(rows)} lines...")
    
    for rowid, line, speaker, chinese_line in rows:
        if not line: continue
        score = calculate_score(line, speaker, chinese_line)
        if score > 0:
            updates.append((score, rowid))
    
    print(f"Injecting {len(updates)} priority scores into DB...")
    cursor.executemany("UPDATE scripts SET priority_score = ? WHERE rowid = ?", updates)
    
    conn.commit()
    print("Optimization Complete! The engine now has its 'Golden Brain'.")
    conn.close()

if __name__ == "__main__":
    main()
