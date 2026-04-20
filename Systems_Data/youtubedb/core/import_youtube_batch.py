import os
import json
import re
import time
import yt_dlp
import subprocess
import sys
import threading

# Initialize global lock for index updates
index_lock = threading.Lock()
from config import DOWNLOAD_DIR, SOURCE_DIR, INDEX_FILE
from utils import clean_srt_to_text, generate_sor_content, openai_client, transcribe_audio_to_srt_large

# Target URL
TARGET_URL = "https://www.youtube.com/watch?v=r7tyCmzZEa8&list=PL68aZEUti9QAlfA1rKmNqZBXL1Yfi6Put&index=1" 

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
        if not result.stdout:
            print("[Error] No output from yt-dlp")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[Error] Failed to get video info: {e}")
        return None

def download_video(video_url, progress_hooks=None):
    """Download video as mp4 with best quality."""
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'ignoreerrors': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if not info: return None, None, None

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
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': str(DOWNLOAD_DIR / f"{video_id}_{sanitize_filename('%(title)s')}.%(ext)s"),
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
            'ignoreerrors': True,
            'progress_hooks': progress_hooks if progress_hooks else [],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return filepath, video_id, clean_title
    except Exception as e:
        print(f"[Error] Failed to download {video_url}: {e}")
        return None, None, None

def transcribe_video(filepath, video_id, title, msg_callback=None):
    """Transcribe video using OpenAI Whisper (with size handling)."""
    srt_filename = f"{video_id}_{title}.srt"
    srt_path = os.path.join(SOURCE_DIR, srt_filename)
    
    if os.path.exists(srt_path):
        print(f"[Skip] SRT already exists: {srt_filename}")
        with open(srt_path, 'r', encoding='utf-8') as f:
            return srt_filename, clean_srt_to_text(f.read())

    if not openai_client:
        print("[Error] OpenAI Client not configured.")
        return None, None

    # Step 1: Extract Audio (to reduce size)
    temp_audio = os.path.join(DOWNLOAD_DIR, f"{video_id}_temp.mp3")
    print(f"[Audio] Extracting audio from {video_id}...")
    try:
        # 使用 ffmpeg 提取 128k mp3 以在保持音質的前提下大幅縮小體積
        cmd = [
            'ffmpeg', '-y', '-i', filepath,
            '-vn', '-ar', '44100', '-ac', '2', '-b:a', '128k',
            temp_audio
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"[Error] Audio extraction failed: {e}")
        return None, None

    # Step 2: Check size and Transcribe
    try:
        audio_size = os.path.getsize(temp_audio)
        if audio_size > 24 * 1024 * 1024:  # > 24MB (OpenAI limit is 25MB)
            print(f"[Large] Audio is {audio_size/1024/1024:.2f}MB, using split transcription...")
            srt_transcript = transcribe_audio_to_srt_large(temp_audio, str(DOWNLOAD_DIR), str(SOURCE_DIR), f"{video_id}_{title}", msg_callback=msg_callback)
            if not srt_transcript:
                return None, None
        else:
            print(f"[Whisper] Sending {audio_size/1024/1024:.2f}MB audio to OpenAI...")
            with open(temp_audio, "rb") as audio_file:
                srt_transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="srt"
                )
        
        # Save SRT
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_transcript)
            
        print(f"[Done] Transcribed: {srt_filename}")
        # Clean up temp audio
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
            
        return srt_filename, clean_srt_to_text(srt_transcript)
    except Exception as e:
        print(f"[Error] Transcription failed: {e}")
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        return None, None

def update_index(video_id, srt_filename):
    """Update videos.json index (Thread-safe)."""
    with index_lock:
        try:
            data = {}
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                    try: data = json.load(f)
                    except json.JSONDecodeError: data = {}
            
            data[srt_filename] = video_id
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"[Index] Updated {INDEX_FILE}")
        except Exception as e:
            print(f"[Error] Failed to update index: {e}")

def process_single_video(url):
    """Pipeline for a single video."""
    filepath, video_id, clean_title = download_video(url)
    if not filepath: return
    
    srt_filename, transcript_text = transcribe_video(filepath, video_id, clean_title)
    if not srt_filename: return
    
    strategy_content = generate_sor_content(clean_title, transcript_text)
    strategy_path = os.path.join(SOURCE_DIR, srt_filename.replace(".srt", "_strategy.txt"))
    with open(strategy_path, 'w', encoding='utf-8') as f:
        f.write(strategy_content)
    
    update_index(video_id, srt_filename)

def main():
    print("=== Library Builder Batch Started (Optimized) ===")
    info = get_video_info(TARGET_URL)
    if info is None: return

    if 'entries' in info:
        entries = list(info['entries'])
        print(f"Found {len(entries)} videos in playlist.")
        for entry in entries:
            video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
            process_single_video(video_url)
    else:
        process_single_video(TARGET_URL)

if __name__ == "__main__":
    main()
