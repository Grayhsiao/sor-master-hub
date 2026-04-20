import os
import yt_dlp
from openai import OpenAI
from dotenv import load_dotenv
import re
import time

# 載入環境變數
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 任務設定 (繼承原本的邏輯)
TASKS = [
    {
        "url": "https://www.youtube.com/watch?v=SPskyx3VnN4&list=PL68aZEUti9QC203GVgR7kLi4oAczk9rcj",
        "series_name": "師資班｜科學實證英文學習系統",
        "skip_indices": [9] 
    }
]

OUTPUT_DIR = "knowledge_base"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_audio(video_id, title):
    safe_title = sanitize_filename(title)
    output_filename = f"yt_{video_id}"
    expected_file = f"{output_filename}.mp3"
    
    if os.path.exists(expected_file):
        return expected_file

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '64'}],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return expected_file

def process_youtube_to_rag():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    for task in TASKS:
        series = task['series_name']
        url = task['url']
        
        print(f"🎬 正在處理系列：{series}")
        
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            entries = result.get('entries', [result])

        for i, entry in enumerate(entries):
            if i+1 in task.get('skip_indices', []): continue
            
            video_id = entry['id']
            title = entry['title']
            print(f"  -> 處理影片: {title}")
            
            # 下載音訊
            mp3_path = download_audio(video_id, title)
            
            # 轉錄
            with open(mp3_path, "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f, language="zh")
            
            # 產出 AI 文案 (模擬蕭博士)
            prompt = f"你是蕭博士，請根據以下逐字稿寫出一篇約 300 字的教學文案。開頭加上 🌟 標題，結尾加上 👉 行銷建議。逐字稿：{transcript.text[:4000]}"
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "用專業且溫暖的口吻寫作"}, {"role": "user", "content": prompt}]
            )
            
            # 儲存到 knowledge_base (升級點：不再塞入單一資料庫，而是獨立檔案)
            output_file = os.path.join(OUTPUT_DIR, f"yt_{series}_{i+1}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.choices[0].message.content)
            
            print(f"  ✅ 已匯入向量資料庫來源：{output_file}")
            
            # 刪除暫存 MP3 (可選)
            if os.path.exists(mp3_path): os.remove(mp3_path)

if __name__ == "__main__":
    process_youtube_to_rag()
