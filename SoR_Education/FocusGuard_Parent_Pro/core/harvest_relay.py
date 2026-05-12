import os
import time
import json
import requests
import threading
import subprocess
import yt_dlp
import platform

# 從同級目錄導入配置
try:
    import core.config as config
except ImportError:
    import config

# 轉接目標 (伺服器位址)
RELAY_API_BASE = "https://sor14.duckdns.org"

def sanitize_filename(name):
    import re
    return re.sub(r'[\\/*?:"<>|]', "", name)

class HarvestRelay:
    def __init__(self):
        self.is_running = True
        print(f"🎬 YouTube 採收轉接員已啟動 (伺服器: {RELAY_API_BASE})")

    def run_loop(self):
        while self.is_running:
            try:
                # 1. 領取任務
                response = requests.get(f"{RELAY_API_BASE}/get_harvest_task", timeout=10, verify=False)
                if response.ok:
                    task = response.json()
                    if task.get("status") == "processing":
                        url = task.get("url")
                        print(f"🚀 接收到新採收任務: {url}")
                        self.process_task(url)
                    else:
                        # 沒有任務，休息一下
                        pass
                else:
                    print(f"⚠️ 無法連線至通訊中心: {response.status_code}")
            except Exception as e:
                print(f"❌ 轉接迴圈異常: {e}")
            
            time.sleep(15)

    def process_task(self, url):
        try:
            print(f"📥 正在下載影片: {url}")
            
            # 使用本機的 yt-dlp
            # 這裡我們下載到本機的臨時資料夾
            tmp_dir = os.path.expanduser("~/Downloads/FocusGuard_Harvest")
            os.makedirs(tmp_dir, exist_ok=True)
            
            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best[height<=720]',
                'outtmpl': os.path.join(tmp_dir, '%(id)s_%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                title = sanitize_filename(info['title'])
                ext = info.get('ext', 'mp4')
                local_file = os.path.join(tmp_dir, f"{video_id}_{title}.{ext}")
                
                if os.path.exists(local_file):
                    print(f"✅ 下載成功: {title}，準備上傳至伺服器...")
                    self.upload_to_server(url, local_file, f"{video_id}_{title}.{ext}", "video")
                    
                    # 如果有字幕，也可以順便下載上傳 (選配)
                    # 這裡先以上傳影片為主，讓伺服器端的 Whisper 去跑
                    print(f"🎉 {title} 處理完成！")
                    
                    # 刪除本機臨時檔以節省空間
                    os.remove(local_file)
                else:
                    print(f"❌ 下載完成但找不到檔案: {local_file}")

        except Exception as e:
            print(f"❌ 處理任務失敗 ({url}): {e}")

    def upload_to_server(self, url, file_path, filename, file_type):
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                data = {
                    'url': url,
                    'type': file_type,
                    'filename': filename
                }
                r = requests.post(f"{RELAY_API_BASE}/upload_harvest_result", files=files, data=data, verify=False)
                if r.ok:
                    print(f"☁️ 檔案已同步至伺服器: {filename}")
                else:
                    print(f"❌ 上傳失敗: {r.status_code}")
        except Exception as e:
            print(f"❌ 上傳過程出錯: {e}")

def start_harvest_relay():
    relay = HarvestRelay()
    relay.run_loop()

if __name__ == "__main__":
    start_harvest_relay()
