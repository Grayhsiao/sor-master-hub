import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class PrizeManager:
    """
    負責從「財政部稅務入口網」抓取中獎號碼並進行對獎
    """
    def __init__(self):
        self.url = "https://invoice.etax.nat.gov.tw/"
        self.winning_numbers = {} # { 'period': { 'special': '...', 'grand': '...', 'first': [...] } }

    def fetch_winning_numbers(self):
        """
        爬取官方網頁獲取最新兩期的中獎號碼
        """
        try:
            response = requests.get(self.url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 定義開獎區塊
            # 官方頁面通常有「本期」與「上期」
            periods = soup.find_all('h2', class_='etw-period')
            tables = soup.find_all('table', class_='etw-table-bg')
            
            for i in range(min(len(periods), 2)):
                period_text = periods[i].get_text(strip=True) # 例如 "112年11-12月"
                # 轉為 YYYY-MM 格式供簡化比較 (這裡簡化處理)
                
                rows = tables[i].find_all('tr')
                data = {
                    'special': rows[1].find('span', class_='etw-color-red').get_text(strip=True), # 特別獎
                    'grand': rows[2].find('span', class_='etw-color-red').get_text(strip=True),   # 特獎
                    'first': [n.strip() for n in rows[3].get_text().split('\n') if len(n.strip()) == 8] # 頭獎 (多組)
                }
                self.winning_numbers[period_text] = data
            return True
        except Exception as e:
            print(f"Fetch Prize Error: {e}")
            return False

    def get_period_from_date(self, date_str):
        """
        從日期 YYYY-MM-DD 找出對應的發票期別 (例如: 113年01-02月)
        """
        try:
            dt = datetime.strptime(date_str.split(' ')[0], "%Y-%m-%d")
            tw_year = dt.year - 1911
            month = dt.month
            start_month = month - 1 if month % 2 == 0 else month
            end_month = start_month + 1
            return f"{tw_year}年{start_month:02d}-{end_month:02d}月"
        except:
            return None

    def check_prize(self, invoice_number, invoice_date=None):
        """
        對獎邏輯
        """
        if not self.winning_numbers:
            self.fetch_winning_numbers()
        
        target_period = self.get_period_from_date(invoice_date) if invoice_date else None
        
        # 找找看這個號碼在哪一期出現
        found_in_any_period = False
        
        for period, numbers in self.winning_numbers.items():
            # 如果有提供日期，我們先檢查這張發票是否屬於這一期
            if target_period and target_period != period:
                continue
            
            found_in_any_period = True
            
            # 1. 特別獎 (全中) 1000萬
            if invoice_number == numbers['special']:
                return True, f"🎉 1000萬 (特別獎)！太強了！\n({period})"
            
            # 2. 特獎 (全中) 200萬
            if invoice_number == numbers['grand']:
                return True, f"🎊 200萬 (特獎)！恭喜！\n({period})"
            
            # 3. 頭獎及其他獎 (從末位開始比)
            for first in numbers['first']:
                if invoice_number == first:
                    return True, f"💰 20萬元 (頭獎)！\n({period})"
                if invoice_number[-7:] == first[-7:]:
                    return True, f"💰 4萬元 (二獎)！\n({period})"
                if invoice_number[-6:] == first[-6:]:
                    return True, f"💰 1萬元 (三獎)！\n({period})"
                if invoice_number[-5:] == first[-5:]:
                    return True, f"💰 4千元 (四獎)！\n({period})"
                if invoice_number[-4:] == first[-4:]:
                    return True, f"💰 1千元 (五獎)！\n({period})"
                if invoice_number[-3:] == first[-3:]:
                    return True, f"🧧 200元 (六獎)！\n({period})"
        
        if target_period and target_period not in self.winning_numbers:
            # 檢查是否太舊或太新 (尚未開獎)
            # 簡單邏輯：如果當前日期小於 target_period 對應的單數月25號，則尚未開獎
            # 這裡為了簡化，直接回傳尚未開獎或不在範圍內
            return False, f"這期 ({target_period}) 尚未開獎或已過期喔！"
            
        return False, "再接再厲，下一張就會中！💪"

prize_manager = PrizeManager()

if __name__ == "__main__":
    pm = PrizeManager()
    if pm.fetch_winning_numbers():
        print("最新期別:", list(pm.winning_numbers.keys())[0])
        print("號碼預覽:", pm.winning_numbers[list(pm.winning_numbers.keys())[0]])
