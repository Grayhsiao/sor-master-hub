import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

KNOWLEDGE_DIR = "knowledge_base"

def smart_split_content(file_path):
    """
    讀取內容，請 AI 進行邏輯分段並加上標記
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 如果已經有很多顆星星，代表可能處理過了
    if content.count('🌟') > 5:
        print(f"Skipping {file_path}: Already segmented.")
        return

    print(f"🧠 正在為 {os.path.basename(file_path)} 進行 AI 智能切片...")

    prompt = f"""
    你是一位專業的「知識架構師」。請閱讀下方的【逐字稿內容】，並將其改寫為多個「精確的知識點」。
    
    【改寫要求】：
    1. **邏輯分段**：在內容發生觀念轉折、主題切換時，插入一個 `🌟` 符號。
    2. **加上標題**：在 `🌟` 後方加上一個【簡短精悍】的標題。
    3. **內容保持原意**：內容文字請保持蕭博士的原話邏輯，不要過度刪減或加戲。
    4. **輸出格式**：
       🌟 【標題A】
       內容文字...
       
       🌟 【標題B】
       內容文字...
    
    【逐字稿內容】：
    {content}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "你專長於知識結構化與精確分段。"}, {"role": "user", "content": prompt}]
        )
        
        # 覆蓋原檔案
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)
        
        print(f"✅ 完成智能切片：{file_path}")
        return True
    except Exception as e:
        print(f"❌ 處理 {file_path} 失敗: {e}")
        return False

def run_smart_chunker():
    files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".txt")]
    for filename in files:
        file_path = os.path.join(KNOWLEDGE_DIR, filename)
        # 針對較長的檔案進行處理
        if os.path.getsize(file_path) > 1000:
            smart_split_content(file_path)
            time.sleep(1) # 避開 Rate Limit

if __name__ == "__main__":
    run_smart_chunker()
