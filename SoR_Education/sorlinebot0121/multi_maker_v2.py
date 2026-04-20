import os
import shutil
import datetime
import re
import yt_dlp
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 📂 設定檔案輸出的資料夾名稱
OUTPUT_DIR = "downloaded_files"

# 💾 資料庫檔案名稱
DB_FILE = "database.txt"

TASKS = [
    # ---------------------------------------------------
    # 1. 既有的親子天下系列
    # ---------------------------------------------------
    {
        "url": "https://www.youtube.com/live/C2nrP4EYiug?si=gcw_fsjjOy5hVQqU",
        "series_name": "SoR 第一階 PA 能如何改善108課綱",
        "skip_indices": []
    },
    

    # ---------------------------------------------------
    # 2. 新加入的影片
    # ---------------------------------------------------
    

    # ---------------------------------------------------
    # ⚠️ 待補區：請填入真正的 YouTube 網址後，取消註解 (#)
    # ---------------------------------------------------
    # {
    #     "url": "https://www.youtube.com/live/C2nrP4EYiug",
    #     "series_name": "SoR 第一階 PA 能如何改善108課綱｜SoR 科普系列講座",
    #     "skip_indices": []
    # },
    # {
    #     "url": "請貼上_GoogleDoc裡的_YouTube_網址",
    #     "series_name": "科普講座 大蒨NOTION筆記",
    #     "skip_indices": []
    # },
]

# ==========================================
# 核心功能
# ==========================================
client = OpenAI(api_key=OPENAI_API_KEY)

# 確保輸出資料夾存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"📂 已建立資料夾：{OUTPUT_DIR}")

def create_backup():
    if os.path.exists(DB_FILE):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"database_backup_{timestamp}.txt"
        try:
            shutil.copy(DB_FILE, backup_name)
            return True
        except: return False
    return True

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
            last_series = matches[-1]
            if last_series != current_series_name and not content.endswith("="*40):
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
        'extract_flat': True, 
        'quiet': True, 
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        # 👇 針對 YouTube 403 錯誤的修復
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
        'quiet': True, 
        'no_warnings': True,
        # 👇 針對 YouTube 403 錯誤的修復 (這裡也要加)
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return expected_file
    except Exception as e:
        print(f"   ❌ 下載失敗 (403): {e}")
        return None

def save_transcript_to_file(mp3_path, transcript_text):
    try:
        txt_path = mp3_path.rsplit('.', 1)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"   📝 逐字稿已存檔：{os.path.basename(txt_path)}")
        return True
    except Exception as e:
        print(f"   ⚠️ 逐字稿存檔失敗: {e}")
        return False

def transcribe_audio(file_path):
    print("   ...AI 正在聽寫 (Whisper)...")
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="zh")
        return transcript.text
    except: return None

def generate_marketing_copy(transcript_text, current_number, series_name):
    clean_transcript = transcript_text.replace("音速", "音素")
    print(f"   ...GPT-4o 正在製作「LINE 買單版」文案...")
    prompt = f"""
    你是【蕭博士】的文案助手，也是親切、有耐心的「鄰家專家」。
    你要將逐字稿改寫成適合 LINE OA 推播、能引發共鳴並讓人想買單的內容。

    【核心指令】：
    1. **禁忌**：絕對禁止中英夾雜 (晶晶體)。除非專有名詞 (如 S O R, Phonics)，其餘請用全中文。
    2. **修正**：縮寫請寫成 "S O R" (空一格，無點)。"Phoneme" 必寫成 "音素"。
    3. **風格**：軟性、口語、有對話感。多用比喻 (如：學游泳、炒飯、地基)。
    4. **排版**：為了在 LINE 上好讀，必須強制分成「三個段落」，中間用空行隔開。

    【內容結構要求】：
    🌟 【{series_name}】觀念 {current_number}：(自訂引發好奇的標題)

    (第一段：鉤子與痛點)
    先描述一個家長的焦慮或迷思 (例如：以為丟全美語就好)。
    描述錯誤方法帶來的後果 (例如：孩子像溺水一樣恐懼)。

    (第二段：權威轉折與解方)
    帶入蕭博士的 SOR 原理。
    用生動的比喻 (如：44 個音素就像蝦仁) 解釋為什麼這才是正確基礎。

    (第三段：溫暖呼籲 CTA)
    以 👉 為開頭。
    安撫家長，給予信心，並引導點擊領取更多資訊。

    【逐字稿】：
    {clean_transcript[:4000]}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except: return None

def append_to_database(content):
    try:
        with open(DB_FILE, "a", encoding="utf-8") as f:
            f.write("\n\n" + content + "\n")
        return True
    except: return False

# ==========================================
# 主程式
# ==========================================
print("🚀 全自動「LINE 買單版」生產線啟動 (防呆省錢版)...\n")
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
            # 🔥 關鍵修改：檢查逐字稿是否存在
            txt_path = f_path.rsplit('.', 1)[0] + ".txt"
            if os.path.exists(txt_path):
                print(f"   ⏭️ 發現逐字稿，跳過 AI 處理 (省錢)：{os.path.basename(txt_path)}")
                # 如果這支跳過了，我們要不要增加觀念編號？
                # 通常如果跳過，代表資料庫裡應該有了，所以編號要加回去，保持順序正確
                cur_num += 1
                continue

            # 如果沒有逐字稿，才進行 AI 處理
            text = transcribe_audio(f_path)
            if text:
                save_transcript_to_file(f_path, text)
                res = generate_marketing_copy(text, cur_num, cur_name)
                if res and append_to_database(res):
                    print(f"✅ 成功：觀念 {cur_num}")
                    cur_num += 1
        print("-" * 20)
print("\n🎉 任務完成！")