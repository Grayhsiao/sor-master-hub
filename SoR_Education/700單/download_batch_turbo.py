import requests
import os
import concurrent.futures

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

assets = {
    "she": "https://m.media-amazon.com/images/M/MV5BMjA1OTU0NjY3NF5BMl5BanBnXkFtZTcwNDU3MjA0MQ@@._V1_.jpg",
    "he": "https://m.media-amazon.com/images/M/MV5BMTczNTI2ODUwOF5BMl5BanBnXkFtZTcwMTU0NTgzNA@@._V1_.jpg",
    "it": "https://m.media-amazon.com/images/M/MV5BZDVkZmI0YzAtNTRjyi00YzBmLWJmYTAtMGM0YTAyNDJlYTE1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg",
    "we": "https://m.media-amazon.com/images/M/MV5BMTY3NjY0NTgxN15BMl5BanBnXkFtZTYwODgzNjc3._V1_.jpg",
    "they": "https://m.media-amazon.com/images/M/MV5BMTY2OTc4MDkxMF5BMl5BanBnXkFtZTcwNDA1MDA4NA@@._V1_.jpg",
    "me": "https://m.media-amazon.com/images/M/MV5BMTQzMjgwNTMzOF5BMl5BanBnXkFtZTcwMDQzNDQzMw@@._V1_.jpg",
    "him": "https://m.media-amazon.com/images/M/MV5BMTU3MDA1MzM1NV5BMl5BanBnXkFtZTcwNjY0Njc3._V1_.jpg",
    "us": "https://m.media-amazon.com/images/M/MV5BMTI5Mjg1MzM2NF5BMl5BanBnXkFtZTYwNjY2MTk4._V1_.jpg",
    "them": "https://m.media-amazon.com/images/M/MV5BMTM3NTY0NjA0N15BMl5BanBnXkFtZTcwNjYyNTY3._V1_.jpg",
    "kid": "https://m.media-amazon.com/images/M/MV5BMTY5NjA0MTc2MV5BMl5BanBnXkFtZTcwMTU0NTgzNA@@._V1_.jpg"
}

def download(word, url):
    path = f"補充/{word}_extra_1.jpg"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return f"✅ {word} 下載成功"
    except:
        return f"❌ {word} 下載失敗"

print("🚀 啟動 Turbo 級並行下載...")
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(download, word, url) for word, url in assets.items()]
    for f in concurrent.futures.as_completed(futures):
        print(f.result())
