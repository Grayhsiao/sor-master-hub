import requests
import os
import concurrent.futures

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

# 使用 Unsplash (較友善) 作為速度演示
assets = {
    "me": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?fm=jpg&q=80&w=1080",
    "us": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?fm=jpg&q=80&w=1080",
    "them": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?fm=jpg&q=80&w=1080",
    "kid": "https://images.unsplash.com/photo-1502086223501-7ea6ec79809c?fm=jpg&q=80&w=1080"
}

def download(word, url):
    path = f"補充/{word}_extra_1.jpg"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return f"✅ {word} 下載成功 ({len(r.content)} bytes)"
    except Exception as e:
        return f"❌ {word} 下載失敗: {e}"

print("🚀 啟動 Turbo 級並行下載 (演示版)...")
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(download, word, url) for word, url in assets.items()]
    for f in concurrent.futures.as_completed(futures):
        print(f.result())
