import os
from dotenv import load_dotenv
from vector_service import VectorService
from openai import OpenAI

def run_diagnostic():
    load_dotenv()
    print("=== 蕭博士 Bot 系統診斷 ===")
    
    # 1. 檢查 .env 檔案
    keys = ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET', 'OPENAI_API_KEY']
    for key in keys:
        val = os.getenv(key)
        if not val or val.startswith('您的_'):
            print(f"❌ 缺少設定: {key}")
        else:
            print(f"✅ 已設定: {key} (前四碼: {val[:4]}...)")

    # 2. 測試向量資料庫
    try:
        print("\n--- 測試向量檢索 ---")
        svc = VectorService()
        query = "PA 是什麼？"
        print(f"詢問: {query}")
        result_text, sources = svc.query(query)
        print(f"檢索結果摘要: {result_text[:100]}...")
        print(f"來源編號: {sources}")
        print("✅ 向量檢索功能正常")
    except Exception as e:
        print(f"❌ 向量檢索失敗: {e}")

    # 3. 測試 OpenAI 連線 (如果 Key 已填寫)
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and not api_key.startswith('您的_'):
        try:
            print("\n--- 測試 OpenAI 連線 ---")
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}]
            )
            print("✅ OpenAI API 連線正常")
        except Exception as e:
            print(f"❌ OpenAI API 測試失敗: {e}")

if __name__ == "__main__":
    run_diagnostic()
