import google.generativeai as genai
import os
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

class GeminiManager:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def parse_bookkeeping_content(self, content_path=None, text_content=None, mime_type=None):
        """
        使用 Gemini 解析記帳內容。
        支援文字、圖片 (收據、帳單截圖)、語音。
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"""
        你是一位專業的記帳助理。請從提供的內容中提取記帳資訊。
        
        請注意：
        1. 可能包含單筆收據，也可能包含多筆交易的「信用卡帳單截圖」。
        2. 請務必以 JSON 格式回傳一個「列表書組」，包含多個交易物件。
        3. 每個交易物件包含以下欄位：
           {{
               "category": "類別 (例如：晚餐, 交通, 購物...)",
               "amount": 金額 (數字),
               "note": "備註 (如果沒有則留空)",
               "date": "YYYY-MM-DD (如果是帳單，請抓取帳單日期；若是單筆記帳且無日期，則使用當前時間 {current_time})",
               "invoice_number": "8位發票號碼 (例如：12345678)，如果沒看到則留空"
           }}
        4. 如果是整張收據，請提取總金額。
        5. 如果是信用卡帳單表格，請提取每一列的消費紀錄。
        
        回傳範例：
        [
          {{"category": "午餐", "amount": 150, "note": "麥當勞", "date": "2024-02-16"}},
          {{"category": "交通", "amount": 500, "note": "加油", "date": "2024-02-15"}}
        ]
        """

        contents = [prompt]
        
        if content_path and os.path.exists(content_path):
            with open(content_path, "rb") as f:
                data = f.read()
            contents.append({
                "mime_type": mime_type,
                "data": data
            })
        
        if text_content:
            contents.append(text_content)

        try:
            response = self.model.generate_content(contents)
            text_response = response.text
            # 提取 JSON 列表
            if '```json' in text_response:
                json_str = text_response.split('```json')[1].split('```')[0].strip()
            else:
                json_str = text_response.strip()
            
            result = json.loads(json_str)
            # 確保回傳一定是列表
            if isinstance(result, dict):
                return [result]
            return result
        except Exception as e:
            print(f"Gemini Parsing Error: {e}")
            return []

if __name__ == "__main__":
    # 簡單測試合法性
    gm = GeminiManager()
    print("Gemini Manager 載入成功")
