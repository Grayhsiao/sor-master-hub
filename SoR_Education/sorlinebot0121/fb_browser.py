import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ==========================================
# 🔧 設定區
# ==========================================
TARGET_ID = '1040899738'  # 您的目標 ID
OUTPUT_FILE = 'fb_real_browser.txt'
SCROLL_TIMES = 50  # 要往下滑幾次？(滑越多抓越多)
# ==========================================

def save_text(text):
    if not text: return
    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n" + "="*50 + "\n")
    except: pass

print("🤖 正在啟動真實瀏覽器模式...")

# 設定 Chrome
chrome_options = Options()
# 關閉通知彈跳視窗
chrome_options.add_argument("--disable-notifications") 
# chrome_options.add_argument("--headless") # 千萬不要開 headless，FB 會發現

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # 1. 前往目標頁面
    target_url = f"https://www.facebook.com/{TARGET_ID}"
    driver.get(target_url)
    
    print("\n🛑 【請注意】")
    print("1. 瀏覽器已開啟。")
    print("2. 如果看到登入畫面，請「手動輸入帳密登入」。")
    print("3. 如果看到驗證畫面，請手動完成驗證。")
    print("4. 確認已經看到對方的貼文後，請回到這裡按下 Enter 鍵，我就會開始工作。")
    
    input("👉 準備好就按 Enter 鍵開始抓取...")
    
    print(f"🚀 開始自動捲動與抓取 (預計執行 {SCROLL_TIMES} 次)...")
    
    scraped_posts = set()
    
    for i in range(SCROLL_TIMES):
        # 抓取目前頁面上的所有貼文區塊
        # FB 的貼文結構很亂，我們抓最通用的文字區塊
        posts = driver.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
        
        count_new = 0
        for post in posts:
            try:
                text = post.text.strip()
                # 過濾掉太短的、已經抓過的
                if len(text) > 10 and text not in scraped_posts:
                    scraped_posts.add(text)
                    save_text(text)
                    print(f"   ✅ 抓到內容：{text[:15]}...")
                    count_new += 1
            except: continue
            
        print(f"⬇️ 第 {i+1}/{SCROLL_TIMES} 次捲動... (本輪新增 {count_new} 篇)")
        
        # 模擬真人往下捲動
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4) # 休息 4 秒等待載入 (太快會轉圈圈)

    print(f"\n🎉 任務完成！內容已存入 {OUTPUT_FILE}")

except Exception as e:
    print(f"❌ 發生錯誤: {e}")

finally:
    # 結束後別急著關，讓你看一下結果，過 10 秒再關
    print("⏳ 10 秒後自動關閉瀏覽器...")
    time.sleep(10)
    driver.quit()