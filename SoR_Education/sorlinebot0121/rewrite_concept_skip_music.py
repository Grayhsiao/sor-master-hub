import os
from openai import OpenAI

# ==========================================
# 📋 設定區
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DOWNLOAD_DIR = "downloaded_files"
TARGET_KEYWORD = "第42堂"

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_content(clean_text):
    print("\n   ✍️ 鎖定目標！正在撰寫文案 (V3 黃金比例版)...")
    
    prompt = f"""
    你是【蕭博士】。
    這是一份已經「精準定位」過後的講座逐字稿。
    
    【任務目標】：
    請找出**「第一個核心觀念」**，並重寫成適合家長閱讀的 LINE 短文。

    【風格要求 (黃金比例)】：
    1. **專業權威 (70%)**：保留 SoR/PA 專業觀念，給家長明確的方向。
    2. **生動比喻 (30%)**：
       * 請優先找文本中的比喻（如副食品、蓋房子）。
       * **如果沒看到**，請務必**模仿博士語氣創造一個**（例如：學英文就像學游泳，要先不怕水...）。
       * 讓家長秒懂「為什麼以前背單字沒用」。

    【輸出格式】：

    === 觀念 1 (精準鎖定版) ===
    
    【標題】：(吸睛標題)

    【博士說重點 (250字)】：
    (請用比喻開場，解釋觀念，並給出專業結論)

    【家長 Q&A (10 組)】：
    1. Q: ...
       A: ...

    ---
    
    【有效內容參考】：
    {clean_text[:50000]} 
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 生成失敗: {e}"

# ==========================================
# 主程式
# ==========================================
print(f"🚀 啟動「互動式瞄準計畫」...")

txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".txt") and TARGET_KEYWORD in f]

if txt_files:
    file_path = os.path.join(DOWNLOAD_DIR, txt_files[0])
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()

    print("\n" + "="*20 + " 🔍 前 1000 字預覽 " + "="*20)
    # 印出前 1000 字，讓使用者找開頭
    print(full_content[:1300])
    print("="*60)
    
    print("\n👇 請在下方輸入(或貼上)你想要開始的「那幾個字」：")
    print("(例如看到『大家晚安』，就輸入『大家晚安』，程式會自動把前面的亂碼切掉)")
    
    # 讓使用者手動輸入瞄準點
    start_phrase = input("請輸入開頭關鍵字：").strip()
    
    if start_phrase:
        # 尋找關鍵字的位置
        start_index = full_content.find(start_phrase)
        
        if start_index != -1:
            print(f"   ✅ 找到了！從第 {start_index} 字開始切割...")
            clean_content = full_content[start_index:]
            
            # 執行生成
            result = generate_content(clean_content)
            
            print("\n" + "="*20 + " 最終成果 " + "="*20)
            print(result)
            print("="*50)
        else:
            print("❌ 找不到這個關鍵字！請確認複製的文字是否正確 (有無空格或標點)。")
    else:
        print("⚠️ 你沒有輸入任何文字，程式將結束。")

else:
    print(f"❌ 找不到檔案！")