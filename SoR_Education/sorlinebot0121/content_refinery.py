import os
import json
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DOWNLOAD_DIR = "downloaded_files"
DB_FILE = "database_knowledge_dynamic.txt"

# 鎖定長影片關鍵字
TARGET_KEYWORD = "第42堂" 

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 第一階段：建築師 (規劃結構) ---
def analyze_structure(full_text):
    print("   🏗️ 正在進行結構分析 (建築師模式)...")
    prompt = f"""
    你是【蕭博士】的內容架構師。
    請閱讀以下長篇逐字稿，並根據內容的「自然邏輯轉折」，將其拆解為適當數量的「核心觀念」。
    
    【要求】：
    1. 不用管時間長度，請依照話題的轉換來分段。
    2. 數量不限，通常 2 小時的演講約在 5~12 個觀念之間。
    3. 請回傳一個 JSON 列表，只包含「標題」與「簡短摘要」。

    【回傳格式範例 (JSON)】:
    {{
        "concepts": [
            {{"title": "觀念1標題", "summary": "簡述..."}},
            {{"title": "觀念2標題", "summary": "簡述..."}}
        ]
    }}

    【逐字稿】：
    {full_text[:60000]} 
    (注意：為了節省運算，這裡只讀前6萬字，通常足夠抓出架構，若影片極長可調整)
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"}, # 強制回傳 JSON
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"   ❌ 結構分析失敗: {e}")
        return None

# --- 第二階段：工班 (細節施工) ---
def generate_detail(full_text, concept_title, concept_summary, index):
    print(f"   🔨 正在施工第 {index} 個觀念：{concept_title} ...")
    
    prompt = f"""
    你是【蕭博士】的知識庫建置員。
    我們已經規劃好一個重點單元，請從「完整逐字稿」中，提取與此單元相關的內容，製作標準問答。

    【當前單元】：
    * 標題：{concept_title}
    * 範圍摘要：{concept_summary}

    【任務】：
    1. **Standard Answer (標準回答)**：撰寫約 200 字的精煉回答，解釋這個觀念。
    2. **Q&A Pairs (問答庫)**：生成 10 組針對這個觀念的問答。

    【輸出格式】：
    ===觀念 {index} : {concept_title}===
    [STANDARD_ANSWER_START]
    (200字回答)
    [STANDARD_ANSWER_END]

    [QUESTIONS_START]
    1. (問題1)
    ...
    10. (問題10)
    [QUESTIONS_END]

    ---
    
    【完整逐字稿】：
    {full_text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"   ❌ 單元 {concept_title} 生成失敗: {e}")
        return None

# ==========================================
# 主程式
# ==========================================
print(f"🚀 啟動「動態架構煉金術」 (鎖定：'{TARGET_KEYWORD}')...")

txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".txt") and TARGET_KEYWORD in f]

if not txt_files:
    print(f"❌ 找不到目標檔案！")
else:
    for txt_file in txt_files:
        file_path = os.path.join(DOWNLOAD_DIR, txt_file)
        with open(file_path, "r", encoding="utf-8") as f:
            full_content = f.read()
            
        # 1. 第一步：分析結構
        structure = analyze_structure(full_content)
        
        if structure and "concepts" in structure:
            concepts = structure["concepts"]
            print(f"   📊 AI 判定本影片共有 {len(concepts)} 個核心觀念。")
            
            # 2. 第二步：逐一生成
            all_results = []
            for i, concept in enumerate(concepts):
                res = generate_detail(full_content, concept["title"], concept["summary"], i+1)
                if res:
                    all_results.append(res)
            
            # 存檔
            if all_results:
                with open(DB_FILE, "a", encoding="utf-8") as f:
                    f.write(f"Source File: {txt_file}\n")
                    f.write(f"AI Auto-Detected Structure: {len(concepts)} concepts\n")
                    f.write("\n\n".join(all_results))
                    f.write("\n" + "="*50 + "\n")
                print(f"✅ 成功！動態生成的 {len(concepts)} 個觀念已存入：{DB_FILE}")

print("\n🎉 任務結束。")