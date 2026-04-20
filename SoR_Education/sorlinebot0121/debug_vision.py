import requests
import http.cookiejar
import os

# ==========================================
# 🔧 設定區
# ==========================================
TARGET_ID = '1040899738' 
COOKIES_FILE = 'cookies.txt'
OUTPUT_HTML = 'robot_see.html'
# ==========================================

print("📸 機器人正在前往現場拍照...")

if not os.path.exists(COOKIES_FILE):
    print("❌ 錯誤：找不到 cookies.txt")
    exit()

try:
    # 1. 讀取您的身分證 (Cookies)
    cookie_jar = http.cookiejar.MozillaCookieJar(COOKIES_FILE)
    cookie_jar.load(ignore_discard=True, ignore_expires=True)

    # 2. 模擬真人瀏覽器的標頭 (偽裝)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # 3. 嘗試進入「手機版」個人頁面 (這是爬蟲最喜歡的路徑)
    url = f"https://mbasic.facebook.com/{TARGET_ID}"
    
    print(f"🔗 連線目標：{url}")
    session = requests.Session()
    response = session.get(url, cookies=cookie_jar, headers=headers)

    # 4. 把機器人看到的畫面存下來
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"\n✅ 拍照完成！已儲存為：{OUTPUT_HTML}")
    print(f"👉 請做這件事：")
    print(f"1. 去您的資料夾找到 '{OUTPUT_HTML}'")
    print(f"2. 用瀏覽器 (Chrome) 打開它")
    print(f"3. 告訴我您看到什麼畫面？")

except Exception as e:
    print(f"💥 發生錯誤: {e}")