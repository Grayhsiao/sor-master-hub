from gsheet_manager import GSheetManager
from datetime import datetime

def test_connection():
    print("正在測試 Google Sheets 連接...")
    gsheet = GSheetManager()
    
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success = gsheet.add_record(date, "測試類別", 0, "這是一則自動生成的測試訊息", "system_test")
    
    if success:
        print("✅ 成功！請檢查你的試算表，應該會看到一筆『測試類別』的紀錄。")
    else:
        print("❌ 失敗。請檢查：")
        print("1. .env 中的 GOOGLE_SHEETS_ID 是否正確。")
        print("2. 試算表是否已共用給服務帳戶 Email。")

if __name__ == "__main__":
    test_connection()
