import sqlite3
import pandas as pd
import io
import requests

def download_csv(url):
    print(f"Downloading {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        return pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    else:
        print(f"Failed to download {url}")
        return None

def main():
    # MELD 官方數據庫連結
    urls = [
        "https://raw.githubusercontent.com/declare-lab/MELD/master/data/MELD/train_sent_emo.csv",
        "https://raw.githubusercontent.com/declare-lab/MELD/master/data/MELD/dev_sent_emo.csv",
        "https://raw.githubusercontent.com/declare-lab/MELD/master/data/MELD/test_sent_emo.csv"
    ]
    
    meld_dfs = []
    for url in urls:
        df = download_csv(url)
        if df is not None:
            meld_dfs.append(df)
            
    if not meld_dfs:
        print("No data downloaded.")
        return
        
    all_meld = pd.concat(meld_dfs)
    print(f"Total MELD utterances: {len(all_meld)}")

    conn = sqlite3.connect('friends_scripts.db')
    cursor = conn.cursor()

    # 為了提速，我們先把匹配鍵 (Season, Episode, Speaker) 做成索引
    # 這裡採取的策略是：Season=S, Episode=E, 然後嘗試模糊比對 Line
    
    count = 0
    for _, row in all_meld.iterrows():
        # 清理台詞字串以利比對
        clean_utterance = row['Utterance'].strip().replace("’", "'").lower()
        
        # 嘗試在我們的資料庫找對應行
        # 我們假設我們的 season, episode 是整數
        cursor.execute('''
            UPDATE scripts 
            SET start_time = ?, end_time = ?, theme = ?, tone = ?
            WHERE season = ? AND episode = ? AND LOWER(line) LIKE ?
            AND (start_time IS NULL OR start_time = '')
        ''', (
            row['StartTime'], 
            row['EndTime'], 
            row['Emotion'], 
            row['Sentiment'],
            row['Season'], 
            row['Episode'], 
            f"%{clean_utterance[:20]}%" # 取前 20 個字做模糊匹配
        ))
        if cursor.rowcount > 0:
            count += cursor.rowcount

    conn.commit()
    print(f"Successfully integrated {count} MELD records with timestamps and emotions.")
    conn.close()

if __name__ == "__main__":
    main()
