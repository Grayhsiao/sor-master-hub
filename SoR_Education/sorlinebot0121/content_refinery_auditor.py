import os
import json
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DOWNLOAD_DIR = "downloaded_files"
OUTPUT_FILE = "database_knowledge_audit.txt" # 輸出的檔案

# 🔥 記得鎖定剛剛切好的乾淨檔案
TARGET_KEYWORD = "_clean" 

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 步驟 1: 分析結構與定位 ---
def analyze_structure(full_text):
    print("   🏗️ 正在規劃章節並鎖定原文位置...")
    prompt = f"""
    你是【蕭博士】的內容編輯。
    請閱讀逐字稿，拆解出核心觀念，並標記每個觀念的「起始句」與「結束句」。
    
    【輸出格式 (JSON Only)】:
    {{
        "concepts": [
            {{
                "title": "觀念標題",
                "start_quote": "請複製該段落的【第一句話】(至少15字，必須完全吻合原文)",
                "end_quote": "請複製該段落的【最後一句話】(至少15字，必須完全吻合原文)"
            }},
            ...
        ]
    }}
    
    【逐字稿 (前 9 萬字)】：
    {full_text[:90000]} 
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"   ❌ 結構分析失敗: {e}")
        return None

# --- 步驟 2: 根據原文生成文案 ---
def generate_content_from_chunk(raw_chunk, title):
    print(f"   ✍️ 正在撰寫文案：{title} ...")
    prompt = f"""
    你是【蕭博士】。我們正在製作 LINE 的教學內容。
    以下是針對「{title}」這個觀念的**原始逐字稿片段**。
    
    【任務】：
    請根據這段原文，撰寫適合家長閱讀的內容。

    【風格要求 (黃金比例)】：
    1. **專業 (70%)**：解釋 SoR/PA 觀念。
    2. **白話 (30%)**：優先使用原文中的比喻。若原文沒比喻，請你模仿博士語氣創造一個。

    【輸出格式】：
    [STANDARD_ANSWER_START]
    (250字左右的精煉文章，含標題、比喻、重點、結論)
    [STANDARD_ANSWER_END]

    [QUESTIONS_START]
    1. Q: ...
       A: ...
    (請生出 10 組)
    [QUESTIONS_END]

    【原始逐字稿片段】：
    {raw_chunk}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"生成失敗: {e}"

# ==========================================
# 主程式
# ==========================================
print(f"🚀 啟動「內容審計版」生成器...")

txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".txt") and TARGET_KEYWORD in f]

if txt_files:
    file_path = os.path.join(DOWNLOAD_DIR, txt_files[0])
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()
    
    print(f"📄 讀取檔案：{os.path.basename(file_path)}")
    
    # 1. 取得結構
    structure = analyze_structure(full_content)
    
    if structure and "concepts" in structure:
        output_path = os.path.join(DOWNLOAD_DIR, OUTPUT_FILE)
        
        with open(output_path, "w", encoding="utf-8") as out_f:
            out_f.write(f"【蕭博士知識庫 - 原文對照審計版】\n")
            out_f.write(f"來源檔案：{os.path.basename(file_path)}\n")
            out_f.write("="*60 + "\n\n")
            
            for i, c in enumerate(structure["concepts"]):
                title = c['title']
                s_quote = c['start_quote']
                e_quote = c['end_quote']
                
                # 2. 擷取原文
                start_idx = full_content.find(s_quote)
                if start_idx != -1:
                    end_idx = full_content.find(e_quote, start_idx) + len(e_quote)
                    # 擷取出來的 raw_text
                    raw_text = full_content[start_idx:end_idx]
                else:
                    raw_text = "(⚠️ 警告：AI 定位失敗，無法擷取原文，請檢查前後文)"

                # 3. 生成成品
                refined_output = generate_content_from_chunk(raw_text, title)
                
                # 4. 寫入檔案 (對照組排版)
                out_f.write(f"📌 觀念 {i+1}：{title}\n")
                out_f.write("="*20 + " 【原始逐字稿 (Raw Data)】 " + "="*20 + "\n")
                out_f.write(raw_text + "\n") # 這裡是原文
                out_f.write("\n" + "="*20 + " 【精煉成品 (Refined Output)】 " + "="*20 + "\n")
                out_f.write(refined_output + "\n") # 這裡是生成的文案
                out_f.write("\n" + "*"*60 + "\n\n\n") # 大分隔線
        
        print(f"\n✅ 審計報告已生成！")
        print(f"📂 請查看：{OUTPUT_FILE}")
        print(f"   (您可以清楚看到 原文 vs 成品 的對照)")

    else:
        print("❌ 結構分析失敗。")

else:
    print(f"❌ 找不到包含 '{TARGET_KEYWORD}' 的檔案！")