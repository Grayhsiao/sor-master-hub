import time
import os
import re
import pickle
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

class FBScraper:
    def __init__(self, target_id='1040899738', output_file='fb_final_posts.txt', rejected_file='fb_rejected_posts.txt'):
        self.target_id = target_id
        self.output_file = output_file
        self.rejected_file = rejected_file
        self.cookie_file = Path(__file__).parent / "fb_cookies.pkl"
        self.min_length = 50
        self.keywords = ["蕭博士", "博士", "英文", "單字", "發音", "SoR", "雙母語", "臺語", "觀念"]
        self.ignore_keywords = ["贊助", "Sponsored", "建議內容", "推薦給你的內容", "Suggested for you"]
        
        self.saved_contents = []
        self.global_index = 1
        self.valid_count = 0
        self.rejected_count = 0
        
        self.driver = None
        self._load_existing_data()

    def _clean_string(self, text):
        t = re.sub(r'\s+', '', text)
        t = t.replace("查看更多", "").replace("SeeMore", "")
        return t

    def _load_existing_data(self):
        if not os.path.exists(self.output_file): return
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                content = f.read()
            posts = content.split('==================================================')
            for post in posts:
                if '【內容】' in post:
                    try:
                        body = post.split('【內容】：')[1].strip()
                        if body: self.saved_contents.append(self._clean_string(body))
                    except: pass
            self.global_index = content.count("【編號】") + 1
            print(f"   ✅ 資料庫已載入 {len(self.saved_contents)} 篇舊文，從第 {self.global_index} 號開始")
        except: pass

    def init_driver(self, headless=False):
        chrome_options = Options()
        chrome_options.add_argument("--disable-notifications")
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option("detach", True)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.set_page_load_timeout(30) # Add timeout to prevent hangs
        return self.driver

    def save_cookies(self):
        if self.driver:
            with open(self.cookie_file, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            print(f"   🍪 Cookies saved to {self.cookie_file}")

    def load_cookies(self):
        if self.driver and self.cookie_file.exists():
            try:
                self.driver.set_page_load_timeout(30)
                self.driver.get("https://www.facebook.com")
                with open(self.cookie_file, "rb") as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                self.driver.refresh()
                print("   🍪 Cookies loaded. Logged in?")
                return True
            except Exception as e:
                print(f"Error loading cookies: {e}")
        return False

    def scrape_posts(self, scroll_limit=10, status_callback=None, clear_rejected=True):
        """核心採收邏輯"""
        self.valid_count = 0     # 重置本次採收計數
        self.rejected_count = 0
        
        if clear_rejected and os.path.exists(self.rejected_file):
            print(f"🧹 正在清空隔離區檔案: {self.rejected_file}")
            open(self.rejected_file, 'w').close()
            
        if not self.driver:
            self.init_driver()
        
        if not self.driver: return # Safety check
        
        target_url = f"https://www.facebook.com/{self.target_id}"
        if self.driver.current_url != target_url:
            try:
                self.driver.get(target_url)
            except Exception as e:
                print(f"Page load timeout or error: {e}")
                if status_callback: status_callback("網頁載入超時，將嘗試繼續...")
        
        print(f"🚀 開始採收 {target_url} ... 等待 5 秒讓網頁載入...")
        time.sleep(5)
        
        consecutive_zero_scrolls = 0
        zero_found_count = 0
        
        for i in range(scroll_limit):
            print(f"--- 開始第 {i+1} 次捲動 ---")
            if status_callback:
                status_callback(f"正在捲動第 {i+1}/{scroll_limit} 次...")
            
            # 1. 展開「查看更多」按鈕並等待
            print("正在展開『查看更多』按鈕...")
            self.driver.execute_script("""
                var articles = document.querySelectorAll("div[role='article']");
                articles.forEach(article => {
                    var buttons = article.querySelectorAll('div[role="button"], span[role="button"]');
                    buttons.forEach(b => {
                        if (b.innerText === "查看更多" || b.innerText === "See more" || b.innerText.includes("...")) {
                            b.click();
                        }
                    });
                });
            """)
            time.sleep(1.5) # 給予足夠時間展開 DOM

            # 2. 抓取主饋送內容 (更精準的標籤與結構分析)
            print("執行 JavaScript 抓取主饋送內容...")
            try:
                posts_data = self.driver.execute_script("""
                    var results = [];
                    var mainFeed = document.querySelector("div[role='main']");
                    if (!mainFeed) mainFeed = document;
                    
                    var articles = mainFeed.querySelectorAll("div[role='article']");
                    articles.forEach(article => {
                        // 1. 嘗試抓取內容主體 (臉書主要訊息標籤)
                        var msgPart = article.querySelector('[data-ad-comet-preview="message"], [data-ad-preview="message"]');
                        var bodyText = msgPart ? msgPart.innerText : "";
                        
                        // 2. 如果沒抓到專用標籤，再退回抓取所有 dir='auto' 的文字
                        if (!bodyText) {
                           var parts = article.querySelectorAll('div[dir="auto"], span[dir="auto"]');
                           var combined = [];
                           parts.forEach(p => combined.push(p.innerText));
                           bodyText = combined.join('\\n');
                        }

                        // 3. 嘗試識別作者 (用來過濾推薦文章)
                        // 通常作者會在第一個 h3 或特定連結中
                        var authorElem = article.querySelector('h3, a[role="link"]');
                        var authorName = authorElem ? authorElem.innerText : "Unknown";

                        if (bodyText && bodyText.length > 30) {
                            results.push({
                                body: bodyText,
                                author: authorName
                            });
                        }
                    });
                    return results;
                """)
            except Exception as e:
                print(f"JS Error: {e}")
                if status_callback: status_callback("❌ 操作瀏覽器發生錯誤，可能已關閉")
                break
                
            print(f"JavaScript 執行完畢，找到 {len(posts_data)} 筆潛在貼文。")
            
            if len(posts_data) == 0:
                zero_found_count += 1
            else:
                zero_found_count = 0
            
            if zero_found_count >= 3:
                print("連續三次未找到內容，可能有登入擋板。")
                if status_callback:
                    status_callback("⚠️ 連續發現 0 篇貼文。請確認瀏覽器是否被「要求登入」的彈出視窗擋住！")
            
            new_found_in_this_scroll = 0
            for post in posts_data:
                # 這裡增加作者過濾邏輯
                if self._save_text(post['body'], author=post['author']):
                    new_found_in_this_scroll += 1
            
            if (new_found_in_this_scroll == 0 and len(posts_data) > 0):
                consecutive_zero_scrolls += 1
            else:
                consecutive_zero_scrolls = 0
            
            print(f"內容存檔完畢。本次新增: {new_found_in_this_scroll} 篇。連續無新增捲動次數: {consecutive_zero_scrolls}")
            
            # 自動捲動
            print("執行 JavaScript 自動捲動...")
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except Exception:
                pass
                
            print("等待 2 秒載入新內容...")
            time.sleep(2) # 等待載入加長一點，確保 FB 載入
            print("等待結束。")
            
            # 如果連續很多次都是重複，可能已經採收完畢
            if consecutive_zero_scrolls >= 5:
                print("   🛑 連續 5 次捲動皆無新內容，可能已達採收終點或碰到底部。")
                if status_callback: status_callback("✅ 偵測到網頁底部或無新文章，提早結束。")
                break

        print(f"📊 採收完成。新增精華：{self.valid_count} 篇，隔離：{self.rejected_count} 篇")

    def _save_text(self, text, author="Unknown"):
        try:
            clean_text = self._clean_string(text)
            
            # 1. 雙向檢查重複：避免 HTML 父子節點（Parent-Child）重疊導致的重複抓取
            for existing in self.saved_contents:
                if clean_text in existing: return False
                if existing in clean_text and len(existing) > 30: return False

            # 2. 作者過濾 (粗略判斷是否與 target_id 相關，或包含常用關鍵字)
            # 如果作者名稱包含 "贊助" 或 "推薦"，通常是推薦文
            if any(ik in author for ik in self.ignore_keywords):
                return False
            
            # 如果是從 target_id 頁面抓的，通常第一個貼文或大部份貼文應該是正確的
            # 這裡我們主要靠關鍵字篩選與 ignore_keywords
            final_content = text.replace("查看更多", "").replace("SeeMore", "").strip()
            
            # 3. 審查機制
            has_keyword = any(kw in text for kw in self.keywords)
            is_ignored = any(ik in text for ik in self.ignore_keywords)
            is_too_short = len(text) < self.min_length
            is_valid_post = has_keyword and not is_too_short and not is_ignored
            
            target_file = self.output_file if is_valid_post else self.rejected_file
            
            with open(target_file, "a", encoding="utf-8") as f:
                if is_valid_post:
                    f.write(f"【編號】：{self.global_index}\n") 
                    f.write(f"【作者】：{author}\n")
                    f.write(f"【字數】：{len(final_content)}\n") 
                else:
                    f.write(f"【被隔離原因】：字數太少({len(final_content)}字) / 關鍵字不符 / 來源疑似雜訊\n")
                    f.write(f"【疑似作者】：{author}\n")
                
                f.write(f"【內容】：\n{final_content}\n")
                f.write("\n" + "="*60 + "\n\n")
            
            self.saved_contents.append(clean_text)
            if len(self.saved_contents) > 1000: self.saved_contents.pop(0)
                
            if is_valid_post:
                self.global_index += 1
                self.valid_count += 1
            else:
                self.rejected_count += 1
                
            return True
        except: return False

if __name__ == "__main__":
    # 保留 CLI 模式方便測試
    scraper = FBScraper()
    scraper.init_driver()
    if not scraper.load_cookies():
        print("請先登入並手動儲存 Cookie")
        input("登入完畢後按 Enter 儲存 Cookie 並開始採收...")
        scraper.save_cookies()
    
    scraper.scrape_posts(scroll_limit=10)
    scraper.driver.quit()