import time
import os
import re
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# 🔧 設定區
# ==========================================
TARGET_ID = '1040899738' 
OUTPUT_FILE = 'fb_final_posts.txt'
MIN_LENGTH = 100 
# ==========================================

print(f"🤖 啟動【多嘴診斷版】...")
print(f"   (特點：它會告訴您為什麼不拍照)")

chrome_options = Options()
chrome_options.add_argument("--disable-notifications") 
chrome_options.add_experimental_option("detach", True) 

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

saved_contents = []
global_index = 1

def clean_string(text):
    t = re.sub(r'\s+', '', text)
    t = t.replace("查看更多", "").replace("SeeMore", "")
    return t

def load_existing_data():
    global global_index
    if not os.path.exists(OUTPUT_FILE): return
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        posts = content.split('==================================================')
        for post in posts:
            if '【內容】' in post:
                try:
                    body = post.split('【內容】：')[1].strip()
                    if body: saved_contents.append(clean_string(body))
                except: pass
        global_index = content.count("【編號】") + 1
        print(f"   ✅ 資料庫已載入 {len(saved_contents)} 篇舊文，從第 {global_index} 號開始")
    except: pass

def save_text(text):
    global global_index
    try:
        # 顯示一點點開頭，證明有讀到
        preview = text[:10].replace('\n', '')
        
        # 1. 檢查長度
        if len(text) < MIN_LENGTH: 
            # print(f"      🔸 太短跳過 ({len(text)}字): {preview}...") 
            return False
        
        clean_text = clean_string(text)
        
        # 2. 檢查重複
        for existing in saved_contents:
            if clean_text in existing: 
                print(f"      🚫 跳過重複: {preview}...")
                return False
            
        # 3. 存檔
        final_content = text.replace("查看更多", "").strip()
        
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"【編號】：{global_index}\n") 
            f.write(f"【字數】：{len(final_content)}\n") 
            f.write(f"【內容】：\n{final_content}\n")
            f.write("\n" + "="*50 + "\n\n")
        
        # 加入記憶
        saved_contents.append(clean_text)
        if len(saved_contents) > 500: saved_contents.pop(0)
            
        global_index += 1
        print(f"   📸 咔嚓！已存第 {global_index-1} 篇 (開頭: {preview}...)")
        return True
    except: return False

# ==========================================
# 主程式
# ==========================================
try:
    load_existing_data()
    driver.get(f"https://www.facebook.com/{TARGET_ID}")
    
    print("\n🛑 【操作說明】")
    print("1. 請手動登入。")
    print("2. 請直接滑到【還沒抓過的】年份或區域。")
    print("3. 如果您測試上面的文章，它顯示「🚫 跳過重複」是正常的！")
    
    input("👉 準備好就按 Enter 鍵...")
    print(f"🚀 診斷開始，請滑動...")

    while True:
        try:
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
                save_text(text)
            
            time.sleep(0.2)
            
        except KeyboardInterrupt:
            print("\n🛑 任務結束")
            break
        except Exception:
            time.sleep(0.5)

except Exception as e:
    print(f"❌ 錯誤: {e}")