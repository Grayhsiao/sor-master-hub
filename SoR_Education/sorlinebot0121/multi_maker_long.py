import os
import shutil
import datetime
import re
import math
import yt_dlp
from openai import OpenAI
from pydub import AudioSegment  # 👈 新朋友：負責切音檔

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 📂 設定檔案輸出的資料夾名稱
OUTPUT_DIR = "downloaded_files"
DB_FILE = "database.txt"

TASKS = [
    # 您可以在這裡放長影片，例如 2 小時的
    {
        "url": "https://www.youtube.com/watch?v=sUxffTDH8LQ&t=1s", 
        "series_name": "與英美同步！搭上最新的 Science of Reading 風潮，用「腦科學」讓學英文變得又快又有趣", 
        "skip_indices": []
    },
]

# ==========================================
# 核心功能
# ==========================================
client = OpenAI(api_key=OPENAI_API_KEY)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def create_backup():
    if os.path.exists(DB_FILE):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy(DB_FILE, f"database_backup_{timestamp}.txt")
        except: pass

def get_next_index(series_name):
    if not os.path.exists(DB_FILE): return 1
    current_max = 0
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            pattern = re.escape(f"【{series_name}】觀念") + r"\s*(\d+)"
            matches = re.findall(pattern, content)
            for m in matches:
                if int(m) > current_max: current_max = int(m)
    except: pass
    return current_max + 1

def smart_separator(current_series_name):
    if not os.path.exists(DB_FILE): return
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content: return
        matches = re.findall(r"【(.*?)】", content)
        if matches:
            if matches[-1] != current_series_name and not content.endswith("="*40):
                with open(DB_FILE, "a", encoding="utf-8") as f:
                    f.write("\n\n" + "="*40 + "\n")
    except: pass

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_playlist_info(url):
    print(f"🔍 正在分析網址...")
    list_id_match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    target_url = url
    if list_id_match:
        target_url = f"https://www.youtube.com/playlist?list={list_id_match.group(1)}"

    ydl_opts = {
        'extract_flat': True, 'quiet': True, 'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    video_list = []
    playlist_title = "未命名系列"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(target_url, download=False)
            if result and 'entries' in result:
                playlist_title = result.get('title', '未命名系列')
                entries = [e for e in result['entries'] if e is not None]
                for entry in entries:
                    video_list.append({'id': entry['id'], 'title': entry.get('title', '無標題')})
            elif result:
                video_list.append({'id': result['id'], 'title': result.get('title', '無標題')})
    except Exception as e:
        print(f"❌ 解析失敗: {e}")
    return video_list, playlist_title

def download_audio(video_info, current_idx, real_concept_number, skip_list):
    if current_idx in skip_list: return "SKIPPED"
    safe_title = sanitize_filename(video_info['title'])
    base_filename = f"觀念{real_concept_number:02d}_{safe_title}"
    output_path_no_ext = os.path.join(OUTPUT_DIR, base_filename)
    expected_file = f"{output_path_no_ext}.mp3"
    
    if os.path.exists(expected_file): 
        print(f"   📂 發現 MP3 舊檔: {expected_file}")
        return expected_file
        
    url = f"https://www.youtube.com/watch?v={video_info['id']}"
    print(f"   ⬇️ 下載中：{safe_title}")
    
    ydl_opts = {
        'format': 'bestaudio/best', 
        'outtmpl': output_path_no_ext, 
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '64'}],
        'quiet': True, 'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return expected_file
    except Exception as e:
        print(f"   ❌ 下載失敗: {e}")
        return None

# 🔥 重點功能：切分音檔與轉錄
def transcribe_large_audio(file_path):
    file_size = os.path.getsize(file_path)
    limit_bytes = 24 * 1024 * 1024  # 設定 24MB 為安全門檻 (OpenAI 限制 25MB)
    
    # 情況 A: 檔案很小，直接跑
    if file_size < limit_bytes:
        print("   ...AI 正在聽寫 (Whisper)...")
        try:
            with open(file_path, "rb") as audio_file:
                return client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="zh").text
        except Exception as e:
            print(f"   ⚠️ 聽寫失敗: {e}")
            return None

    # 情況 B: 檔案太大，啟動「切肉機」
    print(f"   ⚠️ 檔案過大 ({file_size/1024/1024:.2f} MB)，啟動自動切割轉錄模式...")
    
    try:
        audio = AudioSegment.from_mp3(file_path)
        # 設定切分長度：15 分鐘 (比較安全，保證不超過 25MB)
        chunk_length_ms = 15 * 60 * 1000 
        chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
        
        full_transcript = ""
        temp_dir = os.path.join(OUTPUT_DIR, "temp_chunks")
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)
        
        print(f"   🔪 已切分為 {len(chunks)} 個片段，開始逐一處理...")
        
        for i, chunk in enumerate(chunks):
            chunk_name = os.path.join(temp_dir, f"chunk_{i}.mp3")
            chunk.export(chunk_name, format="mp3", bitrate="64k")
            
            print(f"      🎤 正在聽寫第 {i+1}/{len(chunks)} 段...")
            with open(chunk_name, "rb") as audio_file:
                res = client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="zh")
                full_transcript += res.text + " "
            
            # 聽寫完馬上刪除小檔案，節省空間
            os.remove(chunk_name)
            
        # 刪除暫存資料夾
        os.rmdir(temp_dir)
        print("   ✅ 長影片完整聽寫完成！")
        return full_transcript

    except Exception as e:
        print(f"   ❌ 切割處理失敗: {e}")
        return None

def save_transcript_to_file(mp3_path, transcript_text):
    try:
        txt_path = mp3_path.rsplit('.', 1)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"   📝 逐字稿已存檔：{os.path.basename(txt_path)}")
        return True
    except: return False

def generate_marketing_copy(transcript_text, current_number, series_name):
    # 如果文字太長 (超過 5 萬字)，GPT 可能會報錯，這裡做一個簡單的截斷保護
    # 但通常 GPT-4o 可以吃 128k token，應該夠用
    max_chars = 60000 
    if len(transcript_text) > max_chars:
        print(f"   ⚠️ 文字極長 ({len(transcript_text)}字)，將只讀取前 {max_chars} 字以避免當機...")
        
    print(f"   ...GPT-4o 正在製作「LINE 買單版」文案...")
    prompt = f"""
    你是【蕭博士】的文案助手。
    你要將逐字稿改寫成適合 LINE OA 推播、能引發共鳴並讓人想買單的內容。

    【核心指令】：
    1. **禁忌**：絕對禁止中英夾雜。除非專有名詞 (如 S O R, Phonics)。
    2. **修正**：縮寫寫成 "S O R"。"Phoneme" 寫成 "音素"。
    3. **風格**：軟性、口語、有對話感。多用比喻。
    4. **排版**：強制分成「三個段落」，中間用空行隔開。

    【內容結構要求】：
    🌟 【{series_name}】觀念 {current_number}：(自訂引發好奇的標題)

    (第一段：鉤子與痛點)
    先描述一個家長的焦慮或迷思。
    描述錯誤方法帶來的後果。

    (第二段：權威轉折與解方)
    帶入蕭博士的 SOR 原理。
    用生動的比喻解釋為什麼這才是正確基礎。

    (第三段：溫暖呼籲 CTA)
    以 👉 為開頭。
    安撫家長，給予信心，並引導點擊領取更多資訊。

    【逐字稿】：
    {transcript_text[:max_chars]}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"   ❌ 文案生成失敗: {e}")
        return None

def append_to_database(content):
    try:
        with open(DB_FILE, "a", encoding="utf-8") as f:
            f.write("\n\n" + content + "\n")
        return True
    except: return False

# ==========================================
# 主程式
# ==========================================
print("🚀 全自動「長影片特化版」生產線啟動...\n")
create_backup()

for task in TASKS:
    cur_name = task['series_name']
    all_v, _ = get_playlist_info(task['url'])
    print(f"📊 抓取到 {len(all_v)} 支影片") 
    smart_separator(cur_name)
    cur_num = get_next_index(cur_name)

    for i, v_info in enumerate(all_v):
        p_idx = i + 1
        f_path = download_audio(v_info, p_idx, cur_num, task['skip_indices'])
        
        if f_path == "SKIPPED": continue
        if f_path:
            txt_path = f_path.rsplit('.', 1)[0] + ".txt"
            if os.path.exists(txt_path):
                print(f"   ⏭️ 發現逐字稿，跳過 AI 處理：{os.path.basename(txt_path)}")
                cur_num += 1
                continue

            # 使用新的長影片轉錄功能
            text = transcribe_large_audio(f_path)
            
            if text:
                save_transcript_to_file(f_path, text)
                res = generate_marketing_copy(text, cur_num, cur_name)
                if res and append_to_database(res):
                    print(f"✅ 成功：觀念 {cur_num}")
                    cur_num += 1
        print("-" * 20)
print("\n🎉 任務完成！")