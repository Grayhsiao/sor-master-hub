import os
import json
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DOWNLOAD_DIR = "downloaded_files"

# 🔴 請記得修改這裡的關鍵字！
TARGET_KEYWORD = "觀念01_與英美同步" 

# 輸出檔名 1：審計報告 (給人看)
OUTPUT_AUDIT_FILE = "audit_report_dynamic.txt"
# 輸出檔名 2：提示包素材 (給 AI 看)
OUTPUT_PROMPT_FILE = "summary_for_prompt.txt"

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 步驟 1: 動態架構分析 ---
def analyze_structure_dynamic(full_text):
    print("   🧠 正在進行動態結構分析...")
    prompt = f"""
    你是【蕭博士】的內容架構師。
    請閱讀這份逐字稿，根據內容的「自然邏輯轉折」，將其拆解為核心觀念。
    
    【規則】：
    1. 數量不限，依內容多寡決定。
    2. 標記每個觀念的「起始句」與「結束句」。
    
    【輸出格式 (JSON Only)】:
    {{
        "concepts": [
            {{
                "title": "觀念標題",
                "start_quote": "起始句...",
                "end_quote": "結束句..."
            }},
            ...
        ]
    }}
    
    【逐字稿】：
    {full_text[:60000]} 
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

# --- 步驟 2: 生成文案 ---
def generate_content_from_chunk(raw_chunk, title):
    print(f"   ✍️ 正在撰寫文案：{title} ...")
    prompt = f"""
    你是【蕭博士】。
    針對「{title}」這個觀念，請根據以下原文，撰寫適合家長閱讀的教學內容。

    【風格】：
    1. 專業 (70%)：解釋 SoR/PA 觀念。
    2. 白話 (30%)：善用比喻。

    【輸出格式】：
    [STANDARD_ANSWER_START]
    (250字左右的精煉文章)
    [STANDARD_ANSWER_END]
    
    (注意：這裡不需要生成 Q&A，我們只要觀念解釋)

    【原文】：
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
print(f"🚀 啟動「動態審計 + 提示包打包」...")

txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".txt") and TARGET_KEYWORD in f]

if txt_files:
    target_file = txt_files[0]
    file_path = os.path.join(DOWNLOAD_DIR, target_file)
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()
    
    print(f"📄 讀取檔案：{target_file}")
    
    structure = analyze_structure_dynamic(full_content)
    
    if structure and "concepts" in structure:
        concepts = structure["concepts"]
        print(f"   📊 拆解出 {len(concepts)} 個觀念。")
        
        audit_path = os.path.join(DOWNLOAD_DIR, OUTPUT_AUDIT_FILE)
        prompt_path = os.path.join(DOWNLOAD_DIR, OUTPUT_PROMPT_FILE)
        
        # 用來收集所有精華內容的字串
        all_refined_content = ""
        
        with open(audit_path, "w", encoding="utf-8") as audit_f:
            audit_f.write(f"【審計報告】\n來源：{target_file}\n{'='*60}\n\n")
            
            for i, c in enumerate(concepts):
                title = c['title']
                s_quote = c['start_quote']
                e_quote = c['end_quote']
                
                # 擷取原文
                start_idx = full_content.find(s_quote)
                if start_idx != -1:
                    end_idx = full_content.find(e_quote, start_idx)
                    if end_idx != -1:
                        raw_text = full_content[start_idx : end_idx + len(e_quote)]
                    else:
                        raw_text = full_content[start_idx : start_idx + 1500] 
                else:
                    raw_text = "(定位失敗)"

                # 生成精華
                if len(raw_text) > 50:
                    refined_output = generate_content_from_chunk(raw_text, title)
                else:
                    refined_output = "(跳過)"
                
                # 1. 寫入審計報告 (對照用)
                print(f"   ✅ 處理完畢：{title}")
                audit_f.write(f"📌 觀念 {i+1}：{title}\n")
                audit_f.write("="*20 + " 原文 " + "="*20 + "\n")
                audit_f.write(raw_text + "\n\n") 
                audit_f.write("="*20 + " 成品 " + "="*20 + "\n")
                audit_f.write(refined_output + "\n") 
                audit_f.write("\n" + "*"*60 + "\n\n")
                
                # 2. 收集到「提示包」變數中 (只留精華)
                all_refined_content += f"=== 觀念 {i+1}：{title} ===\n"
                all_refined_content += refined_output + "\n\n"

        # 最後將「提示包」寫入檔案
        with open(prompt_path, "w", encoding="utf-8") as prompt_f:
            prompt_f.write(all_refined_content)

        print(f"\n🎉 雙重產出完成！")
        print(f"1️⃣  審計報告 (檢查用)：{OUTPUT_AUDIT_FILE}")
        print(f"2️⃣  提示素材 (出題用)：{OUTPUT_PROMPT_FILE}  <-- 請複製這份檔案的內容！")

    else:
        print("❌ 結構分析失敗。")

else:
    print(f"❌ 找不到關鍵字 '{TARGET_KEYWORD}' 的檔案！")