import os
import sys
from config import OPENAI_API_KEY, GOOGLE_API_KEY, DOWNLOAD_DIR, SOURCE_DIR, DB_PATH
from utils import get_chroma_collection

def verify():
    print("=== 蕭博士 AI 知識庫環境驗證 ===")
    
    # 1. 檢查目錄
    print(f"\n📂 目錄檢查:")
    for name, path in [("下載目錄", DOWNLOAD_DIR), ("來源目錄", SOURCE_DIR), ("資料庫目錄", DB_PATH)]:
        status = "✅ 存在" if os.path.exists(path) else "❌ 缺失"
        print(f"  - {name}: {path} ({status})")
        
    # 2. 檢查 API 金鑰
    print(f"\n🔑 API 金鑰檢查 (從 .env 讀取):")
    openai_ok = "✅ 已設定" if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_") else "❌ 未設定"
    google_ok = "✅ 已設定" if GOOGLE_API_KEY and not GOOGLE_API_KEY.startswith("your_") else "❌ 未設定"
    print(f"  - OpenAI API Key: {openai_ok}")
    print(f"  - Google API Key: {google_ok}")
    
    # 3. 檢查 ChromaDB 連線
    print(f"\n📦 資料庫連線測試:")
    try:
        collection = get_chroma_collection()
        print(f"  - ChromaDB 連線: ✅ 正常 (集合名稱: {collection.name})")
        print(f"  - 目前知識點數量: {collection.count()}")
    except Exception as e:
        print(f"  - ChromaDB 連線: ❌ 失敗 ({e})")

    print("\n" + "="*30)
    print("驗證完成！")

if __name__ == "__main__":
    verify()
