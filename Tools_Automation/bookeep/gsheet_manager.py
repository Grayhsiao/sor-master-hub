import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
from config import MONTHLY_BUDGET
from dotenv import load_dotenv

load_dotenv()

class GSheetManager:
    def __init__(self):
        self.scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.client = self._authenticate()

    def _authenticate(self):
        try:
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=self.scope)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"Error authenticating with Google Sheets: {e}")
            return None

    def add_record(self, date, category, amount, note, user_id, invoice_number=""):
        if not self.client:
            return False
        
        try:
            sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
            sheet.append_row([date, category, amount, note, user_id, invoice_number])
            return True
        except Exception as e:
            print(f"Error adding record to Google Sheets: {e}")
            return False

    def add_records(self, records, user_id):
        """
        批次新增多筆紀錄
        records: [{'date', 'category', 'amount', 'note', 'invoice_number'}, ...]
        """
        if not self.client or not records:
            return False
            
        try:
            sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
            rows = []
            for r in records:
                rows.append([
                    r.get('date'),
                    r.get('category'),
                    r.get('amount'),
                    r.get('note'),
                    user_id,
                    r.get('invoice_number', "")
                ])
            sheet.append_rows(rows)
            return True
        except Exception as e:
            print(f"Error adding batch records to Google Sheets: {e}")
            return False

    def get_summary(self, user_id_list, month=None, is_family=False):
        """
        獲取摘要。支持單一 ID 或 ID 列表。
        """
        if not self.client:
            return "Error: Could not connect to Google Sheets."
        
        # 統一轉為列表處理
        if isinstance(user_id_list, str):
            id_list = [user_id_list]
        else:
            id_list = user_id_list

        try:
            sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
            records = sheet.get_all_records()
            
            if not records:
                return f"你目前在 {target_month} 還沒有任何記帳紀錄喔！"
                
            total = 0
            category_totals = {}
            count = 0
            items = []  # 新增：儲存所有交易細目
            
            target_month = month if month else datetime.now().strftime("%Y-%m")

            # 定義可能的欄位名稱清單
            id_keys = ['User ID', 'user_id', '使用者ID', '使用者 ID', 'UserID']
            amount_keys = ['Amount', 'amount', '金額', '消費']
            date_keys = ['Date', 'date', '日期', '時間']
            category_keys = ['Category', 'category', '類別', '項目']

            def get_value(row_dict, keys, default_idx):
                for k in keys:
                    if k in row_dict:
                        return row_dict[k]
                # 如果都找不到，嘗試根據順序猜測 (Date=0, Cat=1, Amt=2, Note=3, ID=4)
                vals = list(row_dict.values())
                if len(vals) > default_idx:
                    return vals[default_idx]
                return None

            def _get_val_by_idx(row_dict, idx):
                vals = list(row_dict.values())
                return vals[idx] if len(vals) > idx else None
            self._get_val_by_idx = _get_val_by_idx # 導出給外部使用

            for r in records:
                r_user_id = str(get_value(r, id_keys, 4) or "")
                r_amount = get_value(r, amount_keys, 2)
                r_date = str(get_value(r, date_keys, 0) or "")
                
                # 檢查 User ID 是否在清單中
                if r_user_id in id_list and r_date.startswith(target_month):
                    try:
                        amt = float(r_amount)
                        total += amt
                        count += 1
                        
                        # 按類別統計
                        cat = str(get_value(r, category_keys, 1) or '未分類')
                        category_totals[cat] = category_totals.get(cat, 0) + amt

                        # 儲存明細
                        items.append({
                            "date": r_date,
                            "category": cat,
                            "amount": amt,
                            "note": str(get_value(r, ['Note', 'note', '備註', '說明'], 3) or "")
                        })
                    except (ValueError, TypeError):
                        continue
            
            if count == 0:
                return f"你目前在 {target_month} 還沒有任何記帳紀錄喔！"
            
            title = f"{target_month} 家庭合併報表" if is_family else f"{target_month} 個人報表"
            cat_details = "\n".join([f"• {k}: {v}元" for k, v in category_totals.items()])
            
            return {
                "title": title,
                "month": target_month,
                "total": total,
                "count": count,
                "category_details": category_totals,
                "items": items,
                "budget": MONTHLY_BUDGET,
                "remaining": MONTHLY_BUDGET - total,
                "text_summary": f"📊 {title}：\n━━━━━━━━━━\n預算：{MONTHLY_BUDGET}\n總支出：{total} 元\n剩餘：{MONTHLY_BUDGET - total} 元\n筆數：{count} 筆\n\n類別明細：\n{cat_details}"
            }
        except Exception as e:
            print(f"Error getting summary: {e}")
            return "無法獲取摘要資料，請確認試算表格式。"
