import time
import os
import re
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# 🔧 設定與主程序封裝區
# ==========================================

def run_scraper(target_id='1040899738', min_length=100, log_func=print):
    output_file = 'fb_final_posts.txt'
    saved_contents = []
    
    def clean_string(text):
        t = re.sub(r'\s+', '', text)
        t = t.replace("查看更多", "").replace("SeeMore", "")
        return t

    def load_existing_data():
        if not os.path.exists(output_file): return 1
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
            posts = content.split('==================================================')
            for post in posts:
                if '【內容】' in post:
                    try:
                        body = post.split('【內容】：')[1].strip()
                        if body: saved_contents.append(clean_string(body))
                    except: pass
            return content.count("【編號】") + 1
        except: return 1

    def save_text(text, current_index):
        try:
            preview = text[:10].replace('\n', '')
            if len(text) < min_length: return False, current_index
            clean_text = clean_string(text)
            for existing in saved_contents:
                if clean_text in existing: 
                    log_func(f"      🚫 跳過重複: {preview}...")
                    return False, current_index
            
            final_content = text.replace("查看更多", "").strip()
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"【編號】：{current_index}\n") 
                f.write(f"【字數】：{len(final_content)}\n") 
                f.write(f"【內容】：\n{final_content}\n")
                f.write("\n" + "="*50 + "\n\n")
            
            saved_contents.append(clean_text)
            if len(saved_contents) > 500: saved_contents.pop(0)
            log_func(f"   📸 咔嚓！已存第 {current_index} 篇 (開頭: {preview}...)")
            return True, current_index + 1
        except: return False, current_index

    log_func(f"🤖 啟動【FB 採收器】...")
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications") 
    chrome_options.add_experimental_option("detach", True) 
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        current_index = load_existing_data()
        log_func(f"   ✅ 資料庫已載入 {len(saved_contents)} 篇舊文，從第 {current_index} 號開始")
        
        driver.get(f"https://www.facebook.com/{target_id}")
        log_func("\n🛑 【操作說明】")
        log_func("1. 請在彈出的瀏覽器中手動登入。")
        log_func("2. 直接滑到【新貼文】區域，系統會自動偵測並存檔。")
        log_func("3. 結束請關閉瀏覽器或在介面停止。")

        while True:
            try:
                # 檢查瀏覽器是否還開啟
                _ = driver.window_handles
                
                visible_texts = driver.execute_script("""
                    var results = [];
                    var all = document.querySelectorAll("div[role='article'], div[role='dialog'], div[dir='auto']");
                    for (var i = 0; i < all.length; i++) {
                        var rect = all[i].getBoundingClientRect();
                        var isVisible = (
                            rect.bottom > 0 &&
                            rect.top < (window.innerHeight || document.documentElement.clientHeight)
                        );
                        if (isVisible && all[i].innerText.length > 50) {
                            results.push(all[i].innerText);
                        }
                    }
                    return results;
                """)
                
                for text in visible_texts:
                    success, next_index = save_text(text, current_index)
                    if success: current_index = next_index
                
                time.sleep(1.0) # 稍微放慢，避免 UI 刷新過快
                
            except Exception as e:
                if "no such window" in str(e).lower() or "target window already closed" in str(e).lower():
                    log_func("🛑 瀏覽器已關閉，停止採收。")
                    break
                time.sleep(1)
                
    except Exception as e:
        log_func(f"❌ 錯誤: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    run_scraper()