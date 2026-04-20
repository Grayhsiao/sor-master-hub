import os
import json
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DOWNLOAD_DIR = "downloaded_files"
TARGET_KEYWORD = "_clean"  # 強制鎖定檔名有 "_clean" 的檔案
TOTAL_MINUTES = 126 # 請輸入影片總長度 (分鐘)，用來推算時間

client = OpenAI(api_key=OPENAI_API_KEY)

def format_time(minutes):
    """把分鐘數轉成 HH:MM:SS 格式"""
    h = int(minutes // 60)
    m = int(minutes % 60)
    s = int((minutes - int(minutes)) * 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def analyze_structure_with_quotes(full_text):
    print("   🏗️ 正在進行結構分析與定位 (建築師模式)...")
    
    prompt = f"""
    你是【蕭博士】的內容導航員。
    請閱讀這份長篇逐字稿，將其拆解為核心觀念，並**標記出每個觀念的起始與結束語句**。
    
    【輸出格式 (JSON Only)】:
    {{
        "concepts": [
            {{
                "title": "觀念1標題",
                "summary": "簡述...",
                "start_quote": "請複製該段落的【第一句話】(至少10個字)",
                "end_quote": "請複製該段落的【最後一句話】(至少10個字)"
            }},
            ...
        ]
    }}

    【注意】：
    1. `start_quote` 和 `end_quote` 必須**完全吻合**逐字稿中的文字，不要自己改寫，否則我找不到位置。
    2. 請依照話題的自然流動來切分。

    【逐字稿】：
    {full_text[:80000]} 
    (讀取前 8 萬字以確保結構完整)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"   ❌ 分析失敗: {e}")
        return None

# ==========================================
# 主程式
# ==========================================
print(f"🚀 啟動「觀念定位導航系統」...")

txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".txt") and TARGET_KEYWORD in f]

if txt_files:
    file_path = os.path.join(DOWNLOAD_DIR, txt_files[0])
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()
        total_chars = len(full_content)
    
    print(f"📄 檔案讀取成功，共 {total_chars} 字。")
    print(f"⏱️ 影片設定長度：{TOTAL_MINUTES} 分鐘")
    
    # 1. 執行 AI 分析
    structure = analyze_structure_with_quotes(full_content)
    
    if structure and "concepts" in structure:
        print("\n" + "="*20 + " 📍 觀念導航地圖 " + "="*20)
        
        for i, c in enumerate(structure["concepts"]):
            title = c['title']
            s_quote = c['start_quote']
            e_quote = c['end_quote']
            
            # 2. 在原文中尋找位置
            start_idx = full_content.find(s_quote)
            end_idx = full_content.find(e_quote)
            
            # 3. 計算推估時間
            # 原理：假設講話速度是均勻的，文字位置百分比 ≈ 時間百分比
            if start_idx != -1:
                start_pct = start_idx / total_chars
                est_start_time = start_pct * TOTAL_MINUTES
                time_str = format_time(est_start_time)
                loc_info = f"約 {time_str} (文字進度 {int(start_pct*100)}%)"
            else:
                loc_info = "⚠️ (找不到引用句，可能 AI 改寫了文字)"

            print(f"\n🔹 【觀念 {i+1}】：{title}")
            print(f"   🕒 推估位置：{loc_info}")
            print(f"   📝 起始句：{s_quote[:30]}...")
            print(f"   📝 結束句：{e_quote[:30]}...")
            
        print("\n" + "="*60)
        print("💡 註：時間為依據字數分佈的「推估值」，僅供參考，可能會有 1-3 分鐘誤差。")

else:
    print(f"❌ 找不到檔案！")