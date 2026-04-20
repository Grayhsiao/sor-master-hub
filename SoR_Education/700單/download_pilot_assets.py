import requests
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

def download_image(url, path):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, stream=True)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ 下載成功: {path} ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"❌ 下載失敗 {path}: {e}")

assets = {
    "I": [
        ("https://hips.hearstapps.com/hmg-prod/images/iron-man-1561561713.jpg", "option1.jpg"),
        ("https://i.pinimg.com/736x/e0/e1/11/e0e11111111111111111111111111111.jpg", "option2.jpg"), # Placeholder or direct pin
        ("https://m.media-amazon.com/images/M/MV5BMTczNTI2ODUwOF5BMl5BanBnXkFtZTcwMTU0NTgzNA@@._V1_.jpg", "option3.jpg")
    ],
    "you": [
        ("https://m.media-amazon.com/images/M/MV5BMjA1OTU0NjY3NF5BMl5BanBnXkFtZTcwNDU3MjA0MQ@@._V1_.jpg", "option1.jpg"),
        ("https://www.looper.com/img/gallery/the-scene-robert-downey-jr-refused-to-film-for-avengers-endgame/intro-1589380961.jpg", "option2.jpg"),
        ("https://lumiere-a.akamaihd.net/v1/images/open-uri20150422-20810-109v9re_80489955.jpeg", "option3.jpg")
    ],
    "friend": [
        ("https://m.media-amazon.com/images/I/61m1hS0A09L._AC_SL1001_.jpg", "option1.jpg"),
        ("https://m.media-amazon.com/images/I/71X8k7+7S9L._AC_SL1500_.jpg", "option2.jpg"),
        ("https://images.pexels.com/photos/18525/pexels-photo.jpg", "option3.jpg")
    ]
}

for word, options in assets.items():
    dir_path = f"補充/options/{word}"
    os.makedirs(dir_path, exist_ok=True)
    for i, (url, filename) in enumerate(options):
        download_image(url, f"{dir_path}/option{i+1}{os.path.splitext(filename)[1]}")
