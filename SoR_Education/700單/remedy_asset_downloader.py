import requests
import os
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

def download_asset(url, save_path):
    try:
        print(f"📡 補救下載: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        filesize = os.path.getsize(save_path)
        print(f"✅ 下載完成: {save_path} ({filesize} bytes)")
        return True
    except Exception as e:
        print(f"❌ 下載失敗 {url}: {e}")
        return False

# 補救名單
remedy_list = {
    "I": [
        ("https://static.wikia.nocookie.net/marveldatabase/images/3/30/Iron_Man_Vol_1_1.jpg/revision/latest?cb=20171107042036", "option2.jpg"),
        ("https://purepng.com/public/uploads/large/purepng.com-ironman-helmetironman-helmetironman-mask-241519339744vymv0.png", "option3.png")
    ],
    "you": [
        ("https://i.ytimg.com/vi/cR9FMrck4gw/maxresdefault.jpg", "option2.jpg")
    ],
    "friend": [
        ("https://m.media-amazon.com/images/I/81mGKRx4I+L.jpg", "option2.jpg")
    ]
}

print("🚀 開始補救下載任務...")
for word, options in remedy_list.items():
    for i, (url, filename) in enumerate(options):
        save_path = f"補充/options/{word}/{filename}"
        download_asset(url, save_path)
        time.sleep(1)
