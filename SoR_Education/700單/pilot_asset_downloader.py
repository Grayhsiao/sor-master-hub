import requests
import os
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

def download_asset(url, save_path):
    try:
        print(f"📡 正在從 {url} 下載...")
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        filesize = os.path.getsize(save_path)
        if filesize < 1000: # 過小可能是錯誤頁面
            print(f"⚠️ 警告: 檔案過小 ({filesize} bytes)，可能下載不完整或被封鎖。")
            return False
            
        print(f"✅ 下載完成: {save_path} ({filesize} bytes)")
        return True
    except Exception as e:
        print(f"❌ 下載失敗 {url}: {e}")
        return False

# 定義下載清單 (由瀏覽器子代理提供)
asset_list = {
    "I": [
        ("https://www.screengeek.net/wp-content/uploads/2019/07/avengers-endgame-iron-man.jpg", "option1.jpg"),
        ("https://media.comicbook.com/2018/03/iron-man-1-cover-1094054.jpeg", "option2.jpg"),
        ("https://minimalistheroes.com/wp-content/uploads/2014/11/Ironman-Helmet.jpg", "option3.jpg")
    ],
    "you": [
        ("https://images.unsplash.com/photo-1470509037663-253afd7f0f51?fm=jpg&q=80&w=1080", "option1.jpg"),
        ("https://professionalmoron.files.wordpress.com/2015/08/jerry-maguire-hello.jpg", "option2.jpg"),
        ("https://images.wallpapersden.com/image/download/toy-story-woody-buzz-lightyear_65274_1920x1080.jpg", "option3.jpg")
    ],
    "friend": [
        ("https://images.wallpapersden.com/image/download/iconic-yellow-frame-friends-tv-show_65274_1920x1080.jpg", "option1.jpg"),
        ("https://media.architecturaldigest.com/photos/5d80f837130232000885352c/master/pass/Friends_Central_Perk_Couch.jpg", "option2.jpg"),
        ("https://images.unsplash.com/photo-1511632765486-a01980e01a18?fm=jpg&q=80&w=1080", "option3.jpg")
    ]
}

# 執行批次下載
print("🚀 開始試點素材下載任務...")
results = {}

for word, options in asset_list.items():
    print(f"\n--- 處理單字: {word} ---")
    results[word] = []
    for i, (url, filename) in enumerate(options):
        save_path = f"補充/options/{word}/{filename}"
        success = download_asset(url, save_path)
        results[word].append(success)
        time.sleep(1) # 避免請求過快

print("\n📊 下載總體評估：")
for word, stat in results.items():
    s_count = sum(stat)
    print(f"[{word}] 成功: {s_count}/3")
