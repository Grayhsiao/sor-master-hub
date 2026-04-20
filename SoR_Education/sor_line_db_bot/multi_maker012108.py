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
    """每日備份一次"""
    if os.path.exists(DB_FILE):
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        backup_name = f"database_backup_{date_str}.txt"
        try:
            shutil.copy(DB_FILE, backup_name)
            print(f"📦 已更新今日備份: {backup_name}")
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

    ydl_opts = {
        'extract_flat': True, 
        'quiet': True, 
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
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

def download_audio(video_info, current_idx, real_concept_number, skip_list, series_name):
    if current_idx in skip_list: return "SKIPPED"
    
    safe_series = sanitize_filename(series_name)
    safe_title = sanitize_filename(video_info['title'])
    output_filename = f"[{safe_series}]觀念{real_concept_number:02d}_{safe_title}" 
    expected_file = f"{output_filename}.mp3"
    
    if os.path.exists(expected_file): 
        print(f"   📂 發現舊檔: {expected_file}")
        return expected_file
    
    url = f"https://www.youtube.com/watch?v={video_info['id']}"
    print(f"   ⬇️ 下載中: {output_filename}")
    ydl_opts = {
        'format': 'bestaudio/best', 'outtmpl': output_filename,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '64'}],
        'quiet': True, 'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return expected_file
    except: return None

def transcribe_audio(file_path):
    print("   ...AI 正在聽寫 (Whisper)...")
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="zh")
        return transcript.text
    except: return None

def generate_marketing_copy(transcript_text, current_number, series_name):
    clean_transcript = transcript_text.replace("音速", "音素")
    
    print(f"   ...GPT-4o 正在製作「忠於原味教學版」文案...")
    
    # 黃金範例：只作為「語氣」參考，AI 不會抄襲裡面的內容
    golden_example = """
    【黃金風格範例 (請模仿這種語氣，但比喻要用逐字稿裡的)】：
    
    很多家長心裡都很急，覺得學英文就是要趕快把孩子丟到「全美語環境」裡去浸泡。但請試著想像一下：如果一個孩子連閉氣、踢水都還不會，我們就直接把他丟進踩不到底的大海裡，他會有多恐懼？(註：此比喻因逐字稿有提到游泳才使用)
    
    學英文也是一樣的道理。蕭博士強調，我們不能一開始就塞給孩子大量的句子。我們必須從最小的聲音單位——「音素」開始教起。我們先用科學的方法，幫孩子把這 44 個聲音基礎打得穩穩的，讓他有了安全感，之後不管游到哪裡，他都能自信滿滿。
    
    👉 您的孩子是不是也對英文感到抗拒？也許，他只是還沒準備好就「下水」了。我們的課程就像是最有耐心的教練，手把手帶孩子掌握最基本的「聲音積木」，讓學習不再是恐懼的溺水。
    """
    
    opening_styles = [
        "【提問型開頭】：用一個直擊靈魂的問題開場 (例如：您有沒有想過...？為什麼孩子...？)。",
        "【情境型開頭】：直接描述一個具體的崩潰場景 (例如：孩子拿著考卷哭著說...，這時家長通常會...)。",
        "【倒裝/對比型開頭】：先講一個驚人的結論，再回頭解釋原因 (例如：別再逼孩子背單字了，除非...)。",
        "【數據/權威型開頭】：引用蕭博士的觀察或科學事實開場 (例如：蕭博士指出，90% 的學習挫折其實都源自於...)。"
    ]
    
    selected_style = random.choice(opening_styles)

    prompt = f"""
    你是【蕭博士】的「知識轉譯者」，請將逐字稿改寫成一篇**「有觀點、教學感強、開頭有變化」**的 LINE OA 短文。

    【核心原則 (嚴格遵守)】：
    1. **忠於原味 (最重要)**：**嚴格限定**只能使用逐字稿裡真正提到過的例子或比喻！
       - 如果逐字稿說「像學游泳」，你就可以寫游泳。
       - 如果逐字稿完全沒比喻，**請直接用白話文解釋原理**，千萬不要自己編造（嚴禁亂套用蓋房子、炒飯等）。
    2. **拒絕廢話**：內容要紮實，不要寫空泛的推銷詞。
    3. **去標籤化**：直接分段撰寫，不要出現「內容：」等標籤。
    4. **口語化**：**嚴禁使用艱澀的專業術語** (除非是 S O R)。請用「大白話」撰寫，風格要像**鄰居在聊天**一樣軟性、好讀。

    {golden_example}

    【本次寫作任務】：
    請採用 **{selected_style}** 來撰寫第一段。

    【結構要求】：
    **第一段 (80字)**：{selected_style}
    **第二段 (250字)**：【核心教學區】。提取逐字稿中的具體步驟、S O R 原理或數據。**如果有逐字稿比喻就用，沒有就直白解釋**，讓家長秒懂「為什麼要這樣做」。
    **第三段 (80字)**：以 👉 開頭的溫暖建議。告訴家長具體下一步該怎麼調整心態或做法。

    【現在，請針對以下逐字稿進行改寫】：
    🌟 標題格式：🌟 【{series_name}】觀念 {current_number}：(請自訂引發好奇的標題)
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
print("🚀 全自動生產線啟動 (忠於原味版)...")
create_backup()

for task in TASKS:
    cur_name = task['series_name']
    print(f"\n--- 任務：{cur_name} ---")
    
    all_v, yt_title = get_playlist_info(task['url'])
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