from dotenv import load_dotenv

# ==========================================
# 📋 設定區
# ==========================================
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DB_FILE = "database.txt"

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================================
# 核心功能：檔案處理 (含自動存檔)
# ==========================================

def sanitize_filename(name):
    """移除特殊符號"""
    name = re.sub(r'[\\/*?:"<>|【】\[\]｜]', "", name)
    return name.strip()

def transcribe_audio(file_path):
    """MP3 轉文字"""
    print(f"🎤 正在將 MP3 轉錄為逐字稿：{os.path.basename(file_path)}...")
    print("   (這可能需要幾十秒，請稍候...)")
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                language="zh"
            )
        return transcript.text
    except Exception as e:
        print(f"❌ 聽寫失敗: {e}")
        return None

def save_transcript_file(mp3_path, text):
    """【關鍵功能】將轉錄好的文字存檔，下次就不用再聽一次"""
    if not text: return
    txt_filename = mp3_path.replace(".mp3", "_original.txt")
    try:
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"   💾 原始逐字稿已自動保存：{os.path.basename(txt_filename)}")
        print("      (下次修改時將直接讀取此檔案，省時又省錢！)")
    except Exception as e:
        print(f"⚠️ 存檔失敗: {e}")

def select_file_manually(candidates=None):
    """手動選擇檔案"""
    if not candidates:
        audio_files = glob.glob("*.mp3")
        text_files = glob.glob("*_original.txt")
        candidates = sorted(list(set(audio_files + text_files)))

    if not candidates:
        print("❌ 資料夾內找不到相關檔案。")
        return None

    print("\n🔍 為了避免抓錯，請您手動選擇正確的檔案：")
    for i, f in enumerate(candidates):
        print(f"   ({i+1}) {f}")
    
    print("\n👉 請輸入檔案編號 (例如 1)：")
    try:
        sel = int(input("編號：")) - 1
        if 0 <= sel < len(candidates):
            selected_file = candidates[sel]
            
            # 1. 如果選到 txt，直接讀
            if selected_file.endswith(".txt"):
                with open(selected_file, "r", encoding="utf-8") as f:
                    return f.read()
            
            # 2. 如果選到 mp3，聽寫並存檔
            elif selected_file.endswith(".mp3"):
                text = transcribe_audio(selected_file)
                if text:
                    save_transcript_file(selected_file, text) # 存檔
                return text
        else:
            print("❌ 無效編號")
            return None
    except:
        return None

def find_source_material(series, number):
    """智慧搜尋檔案"""
    
    if not str(number).isdigit():
        return select_file_manually()

    num_str = f"{int(number):02d}" # 例如 02
    
    # 1. 先找有沒有現成的 TXT (最快)
    # 我們先找符合系列名的 TXT
    safe_series = sanitize_filename(series)
    keywords = safe_series.replace("師資班", "").replace("英文學習系統", "")
    if not keywords: keywords = safe_series

    all_txt = glob.glob(f"*{num_str}*_original.txt")
    
    # 過濾同系列的 TXT
    matched_txt = [f for f in all_txt if keywords in sanitize_filename(f)]
    
    if matched_txt:
        print(f"   📂 找到現成逐字稿 (不用重聽)：{matched_txt[0]}")
        with open(matched_txt[0], "r", encoding="utf-8") as f:
            return f.read()

    # 2. 如果沒有 TXT，才找 MP3
    print(f"   ...搜尋屬於【{series}】的音檔...")
    all_mp3 = glob.glob(f"*{num_str}*.mp3")
    
    matched_mp3 = [f for f in all_mp3 if keywords in sanitize_filename(f)]

    target_mp3 = None
    if len(matched_mp3) == 1:
        target_mp3 = matched_mp3[0]
        print(f"   📂 精準鎖定 MP3：{target_mp3}")
    elif len(matched_mp3) > 1:
        return select_file_manually(matched_mp3)
    elif all_mp3:
        print(f"   ⚠️  找不到同系列檔案，但發現其他同編號檔案：")
        return select_file_manually(all_mp3)
    else:
        print("   ⚠️  找不到任何檔案。")
        return select_file_manually()

    # 執行聽寫並存檔
    if target_mp3:
        text = transcribe_audio(target_mp3)
        if text:
            save_transcript_file(target_mp3, text) # 存檔
        return text
    
    return None

# ==========================================
# 核心功能：其他 (保持不變)
# ==========================================

def load_concepts_from_db():
    if not os.path.exists(DB_FILE):
        print("❌ 找不到 database.txt")
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f: lines = f.readlines()
    concepts = []
    pattern = r"🌟\s*【(.*?)】(.*)"
    for line in lines:
        line = line.strip()
        match = re.search(pattern, line)
        if match:
            series = match.group(1)
            raw_title = match.group(2).strip()
            num_match = re.search(r"觀念\s*(\d+)[:：]?(.*)", raw_title)
            if num_match:
                number = num_match.group(1)
                title = num_match.group(2).strip()
                if not title: title = raw_title
            else:
                number = "無編號"
                title = raw_title 
            concepts.append({"series": series, "number": number, "title": title, "full_header": line})
    return concepts

def optimize_instruction(raw_input):
    print("✨ AI 秘書正在優化您的指令...")
    prompt = f"使用者修改文案指令：「{raw_input}」。請改寫為給 AI 的「最高指導原則」。1. 轉化為具體的風格限制。2. 禁止事項要用強烈語氣標示「嚴格禁止」。3. 只回傳改寫後的文字。"
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except: return raw_input

def rewrite_article(transcript, optimized_instruction):
    clean_transcript = transcript.replace("音速", "音素")
    print(f"\n🚀 GPT-4o 正在重寫中...")
    prompt = f"""
    你是【蕭博士】的「知識轉譯者」。請修改這篇 LINE OA 文案。
    【⚠️ 最高指導原則】：{optimized_instruction}
    【⛔️ 鐵律】：**絕對禁止自創比喻**：**只能使用逐字稿裡真正提到過的例子**！
    【標準 SOP】：1. **忠於原味**：內容必須基於逐字稿。2. **標記潤飾**：AI加入的修飾語請用 **【 】** 包起來。3. **去標籤化**：直接分段，不要出現標籤。4. **口語化**：講人話。
    【結構要求】：**第一段 (80字)**：吸引人的開頭。**第二段 (250字)**：核心教學區。**第三段 (80字)**：以 👉 開頭的溫暖建議。
    【原始逐字稿】：{clean_transcript[:4000]}
    """
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return None

def update_database(full_header, new_content):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n{'='*20} 修訂版 (針對：{full_header}) {'='*20}\n")
        f.write(new_content)
        f.write(f"\n{'='*50}\n")
    print(f"✅ 已將新版本附加在 {DB_FILE} 的最下方！")

if __name__ == "__main__":
    while True:
        concepts = load_concepts_from_db()
        if not concepts: break
        print("\n" + "="*80)
        print(f"📖 觀念列表 (共 {len(concepts)} 篇)：")
        print("="*80)
        for idx, c in enumerate(concepts):
            num_display = f"觀念 {c['number']}" if c['number'] != "無編號" else "(無編號)"
            print(f"[{idx+1}] 【{c['series']}】{num_display}：{c['title']}")
        print("="*80)
        selection = input("\n請輸入您要修改的「流水號」 (輸入 q 離開)：")
        if selection.lower() == 'q': break
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(concepts):
                target = concepts[idx]
                print(f"\n🎯 您選擇了：{target['full_header']}")
                transcript = find_source_material(target['series'], target['number'])
                if not transcript:
                    print("❌ 未取得逐字稿，取消操作。")
                    continue
                print("\n💡 請輸入您的修改指令：")
                raw_input = input("導演指令：")
                if not raw_input: optimized_prompt = "請依照標準 SOP 重新整理。"
                else: optimized_prompt = optimize_instruction(raw_input)
                print(f"\n👉 AI 指令：{optimized_prompt}")
                new_article = rewrite_article(transcript, optimized_prompt)
                if new_article:
                    print("\n" + "-"*40)
                    print(new_article)
                    print("-"*40 + "\n")
                    if input("保存？(y/n): ").lower() == 'y': update_database(target['full_header'], new_article, optimized_prompt)
            else: print("❌ 無效編號")
        except ValueError: print("❌ 請輸入數字")