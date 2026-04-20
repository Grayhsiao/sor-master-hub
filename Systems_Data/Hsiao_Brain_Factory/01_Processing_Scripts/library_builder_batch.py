import os
import json
import re
import time
import glob
import yt_dlp
import openai
import google.generativeai as genai
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
# Target URL (Modify this variable to change the target)
TARGET_URL = "https://www.youtube.com/watch?v=r7tyCmzZEa8&list=PL68aZEUti9QAlfA1rKmNqZBXL1Yfi6Put&index=1" 

# API Keys（請在終端機 export 或用 .env 設定）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not OPENAI_API_KEY or not GOOGLE_API_KEY:
    print("⚠️  警告：OPENAI_API_KEY 或 GOOGLE_API_KEY 未設定！請設定環境變數後再執行。")


# Directory Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_files")
SOURCE_DIR = os.path.join(BASE_DIR, "sources")
DB_FILE = os.path.join(BASE_DIR, "sor_strategy_db.txt")
INDEX_FILE = os.path.join(BASE_DIR, "videos.json")

# Ensure directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)

# Configure APIs
client = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)


def sanitize_filename(name):
    """Filter special characters for valid filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_video_info(url):
    """Get video info or playlist entries via CLI for robustness."""
    print(f"Analyzing URL: {url}")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--dump-single-json",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"[Warn] yt-dlp returned non-zero: {result.stderr[:200]}...")
        
        if not result.stdout:
            # If ignore-errors is on, empty stdout might mean total failure or empty playlist
            if result.stderr:
                 print(f"[Error] No output from yt-dlp. Stderr: {result.stderr[:200]}")
            else:
                 print("[Error] No output from yt-dlp")
            return None
            
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[Error] Failed to get video info: {e}")
        return None

def download_video(video_url):
    """Download video as mp4 with best quality."""
    
    # First get info to determine filename
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'ignoreerrors': True, 'no_warnings': True}) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
            except Exception:
                # If extract_info fail, maybe private video
                print(f"[Skip] Could not extract info for {video_url} (Private/Deleted?)")
                return None, None, None
            
            if not info:
                return None, None, None

            video_id = info['id']
            title = info.get('title', video_id)
            clean_title = sanitize_filename(title)
            filename = f"{video_id}_{clean_title}.mp4"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

        if os.path.exists(filepath):
            print(f"[Skip] File already exists: {filename}")
            return filepath, video_id, clean_title

        print(f"[Downloading] {title}...")
        
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, f"{video_id}_{sanitize_filename('%(title)s')}.%(ext)s"),
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(filepath):
            print(f"[Error] File not found after download: {filename}")
            return None, None, None
            
        print(f"[Done] Downloaded: {filename}")
        return filepath, video_id, clean_title

    except Exception as e:
        print(f"[Error] Failed to download {video_url}: {e}")
        return None, None, None

def transcribe_video(filepath, video_id, title):
    """Transcribe video using OpenAI Whisper."""
    srt_filename = f"{video_id}_{title}.srt"
    srt_path = os.path.join(SOURCE_DIR, srt_filename)
    
    if os.path.exists(srt_path):
        print(f"[Skip] SRT already exists: {srt_filename}")
        # Read existing content
        transcript_text = ""
        try:
             with open(srt_path, 'r', encoding='utf-8') as f:
                 lines = f.readlines()
                 transcript_text = " ".join([l.strip() for l in lines if not re.match(r'^\d+$|^\d{2}:\d{2}:\d{2}', l) and l.strip()])
        except:
             transcript_text = "(Error reading existing SRT)"
        return srt_filename, transcript_text

    print(f"[Transcribing] {title}...")
    
    try:
        audio_file = open(filepath, "rb")
        
        # Request SRT directly
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="srt"
        )
        srt_transcript = transcript_response
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_transcript)
            
        # Extract plain text from SRT for Gemini
        transcript_text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', srt_transcript)
        transcript_text = transcript_text.replace('\n', ' ').strip()
        
        print(f"[Done] Transcribed: {srt_filename}")
        return srt_filename, transcript_text
        
    except Exception as e:
        print(f"[Error] Transcription failed: {e}")
        return None, None

def generate_sor_content(title, transcript):
    """Generate SOP content using GPT-4o."""
    print(f"[Generative AI] Generating strategy for: {title}...")
    
    prompt = f"""
    你現在要執行【蕭博士 SoR 文案生產 SOP】。
  
    一、 核心戰略
    換殼不換靈魂。靈魂是科學觀念，外殼是針對病徵的比喻。

    二、 生產流程
    1. 輸入：請閱讀下方的逐字稿。
    2. 提煉：抓取科學術語與理論。
    3. 優化：轉化為視覺化比喻 (A)。
    4. 發散：針對優化觀念 A，產出 10 組對應痛點的 Q&A。

    三、 規格要求
    每一組 Q&A 需包含：理論背景、優化觀念、實戰 Q&A。
  
    【影片標題】：{title}
    【逐字稿】：{transcript}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional educational content strategist specializing in the Science of Reading (SoR)."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
        
        # Save to DB
        separator = "="*50 + "\n"
        entry = f"{separator}Video: {title}\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n{separator}\n{content}\n\n"
        
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
            
        print(f"[Done] Content saved to {DB_FILE}")
        return True
    except Exception as e:
        print(f"[Error] GPT-4o generation failed: {e}")
        return False

def update_index(video_id, srt_filename):
    """Update videos.json index."""
    try:
        data = {}
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        
        data[srt_filename] = video_id
        
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"[Index] Updated {INDEX_FILE}")
    except Exception as e:
        print(f"[Error] Failed to update index: {e}")

def process_single_video(url):
    """Pipeline for a single video."""
    # 1. Download
    filepath, video_id, clean_title = download_video(url)
    if not filepath: return
    
    # 2. Transcribe
    srt_filename, transcript_text = transcribe_video(filepath, video_id, clean_title)
    if not srt_filename: return
    
    # 3. Generate Content
    generate_sor_content(clean_title, transcript_text)
    
    # 4. Update Index
    update_index(video_id, srt_filename)

def main():
    print("=== Library Builder Batch Started ===")
    
    if "YOUR_API_KEY" in OPENAI_API_KEY or "YOUR_API_KEY" in GOOGLE_API_KEY:
        print("[Warning] API Keys are not set correctly. Please edit the script or set environment variables.")
    
    info = get_video_info(TARGET_URL)
    
    if info is None:
        print("[Error] Could not fetch info for TARGET_URL")
        return

    # Check if playlist
    if 'entries' in info:
        print(f"[Mode] Playlist Detected: {info.get('title', 'Unknown Playlist')}")
        entries = list(info['entries']) # Handle generator
        print(f"Found {len(entries)} videos.")
        
        for entry in entries:
            # entries in extract_flat are minimal, need full URL
            # entry usually has 'url' or 'id'
            video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
            print(f"\n--- Processing Playlist Item: {entry.get('title')} ---")
            process_single_video(video_url)
            
    elif info.get('_type') == 'video' or 'id' in info:
        print(f"[Mode] Single Video Detected: {info.get('title')}")
        process_single_video(TARGET_URL)
    else:
        print("[Error] Unknown URL type.")

if __name__ == "__main__":
    main()
