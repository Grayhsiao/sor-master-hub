import os
import glob
import shutil
import datetime
import re
import time
import random
import yt_dlp
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

TASKS = [
    {
        "url": "https://www.youtube.com/watch?v=SPskyx3VnN4", # 替換您的網址
        "series_name": "師資班｜QA問答", 
        "skip_indices": []  
    },
]

DB_FILE = "database.txt"

# ==========================================
# 核心功能
# ==========================================
client = OpenAI(api_key=OPENAI_API_KEY)

def create_backup():
    if os.path.exists(DB_FILE):
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        backup_name = f"database_backup_{date_str}.txt"
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
                with open(DB_FILE, "a", encoding="utf-8") as f: f.write("\n\n" + "="*40 + "\n")
    except: pass

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_playlist_info(url):
    print(f"🔍 正在分析網址...")
    list_id_match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    target_url = f"https://www.youtube.com/playlist?list={list_id_match.group(1)}" if list_id_match else url

    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
    video_list = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(target_url, download=False)
            if result and 'entries' in result:
                entries = [e for e in result['entries'] if e is not None]
                for entry in entries:
                    video_list.append({'id': entry['id'], 'title': entry.get('title', '無標題')})
            elif result:
                video_list.append({'id': result['id'], 'title': result.get('title', '無標題')})
    except Exception as e:
        print(f"❌ 解析失敗: {e}")
    return video_list

def download_audio(video_info, current_idx, real_concept_number, skip_list, series_name):
    if current_idx in skip_list: return "SKIPPED"
    
    safe_series = sanitize_filename(series_name)
    safe_title = sanitize_filename(video_info['title'])
    output_filename = f"[{safe_series}]觀念{real_concept_number:02d}_{safe_title}" 
    expected_file = f"{output_filename}.mp3"
    
    if os.path.exists(expected_file): 
        print(f"   📂 發現 MP3: {expected_file}")
        return expected_file
    
    print(f"   ⬇️ 下載 MP3: {output_filename}")
    ydl_opts = {
        'format': 'bestaudio/best', 'outtmpl': output_filename,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '64'}],
        'quiet': True, 'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([f"https://www.youtube.com/watch?v={video_info['id']}"])
        return expected_file
    except: return None

def transcribe_audio(file_path):
    print("   ...AI 正在聽寫 (Whisper)...")
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="zh")
        return transcript.text
    except: return None

# ★★★ 這裡就是「買單版」的靈魂所在 ★★★
def generate_marketing_copy(transcript_text, current_number, series_name):
    clean_transcript = transcript_text.replace("音速", "音素")
    
    print(f"   ...GPT-4o 正在製作「高轉化率銷售文案」...")
    
    opening_styles = [
        "【痛點直擊型】：直接點出家長最焦慮的場景 (例如：看到成績單心都涼了)。",
        "【恐懼訴求型】：如果不現在改變，孩子未來會多辛苦。",
        "【權威認證型】：強調蕭博士的專業與科學背書。",
    ]
    selected_style = random.choice(opening_styles)

    prompt = f"""
    你是【蕭博士】的**「金牌銷售文案」**。請將逐字稿改寫成一篇**極具說服力、以成交為目的**的 LINE OA 短文。

    【核心指令 (銷售導向)】：
    1. **喚醒痛點**：開頭必須狠狠打中家長的焦慮 (發音不準、成績不好、孩子排斥)。
    2. **提供唯一解**：告訴家長，過去的方法都錯了，**蕭博士的 S.O.R. 是唯一的科學救星**。
    3. **行動呼籲 (CTA)**：結尾不要只是溫暖建議，要給出一種「不學就虧大了」或「現在就是改變的時機」的急迫感。
    4. **口語感**：要像一個熱心的顧問在推心置腹地建議，可以使用「買單」、「投資」、「省下補習費」等概念。
    
    【結構要求】：
    **第一段 (80字)**：{selected_style}
    **第二段 (250字)**：【價值展示區】。用逐字稿的內容證明這套系統多有效。**可以適度加入銷售性質的潤飾 (如：省下十年的冤枉路)**。
    **第三段 (80字)**：強力的行動呼籲。

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
        with open(DB_FILE, "a", encoding="utf-8") as f: f.write("\n\n" + content + "\n")
        return True
    except: return False

# ==========================================
# 主程式執行區
# ==========================================
# ★★★ 這裡的文字改回您截圖裡的樣子 ★★★
print("🚀 全自動「LINE 買單版」生產線啟動...")
create_backup()

for task in TASKS:
    cur_name = task['series_name']
    print(f"\n--- 任務：{cur_name} ---")
    
    all_v = get_playlist_info(task['url'])
    print(f"📊 抓取到 {len(all_v)} 支影片")
    
    if not all_v: continue

    smart_separator(cur_name)
    cur_num = get_next_index(cur_name)

    for i, v_info in enumerate(all_v):
        p_idx = i + 1
        print(f"🎬 處理中: {v_info['title']}")
        
        f_path = download_audio(v_info, p_idx, cur_num, task['skip_indices'], cur_name)
        
        if f_path == "SKIPPED": continue
        if f_path:
            text = transcribe_audio(f_path)
            if text:
                res = generate_marketing_copy(text, cur_num, cur_name)
                if res and append_to_database(res):
                    print(f"   ✅ 成功觀念 {cur_num}")
                    cur_num += 1
        print("-" * 20)

print("\n🎉 任務完成！請查看 database.txt。")