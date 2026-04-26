import sys
import os
import time
import json

# --- 啟動日誌 (除錯用) ---
try:
    with open(os.path.expanduser("~/focus_guard_debug.log"), "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 程式啟動中 (正式版)...\n")
except: pass
import threading
import subprocess
import platform
import collections
import webbrowser
import psutil
import requests
import re
import uuid
import tkinter as tk
from tkinter import messagebox, simpledialog
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from tkinter import ttk

# --- 基礎配置 ---
def resource_path(relative_path):
    """ 獲取資源絕對路徑，兼容開發環境與 PyInstaller 打包環境 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

BASE_DIR = resource_path(".")
env_path = resource_path("../../.env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # 嘗試載入同級目錄的 .env (如果有的話)
    load_dotenv(os.path.join(BASE_DIR, ".env"))

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 雲端伺服器位址 (正式版)
SERVER_URL = "https://sor14.duckdns.org/focus_pro"

if not YOUTUBE_API_KEY: YOUTUBE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY: GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

IS_MAC = platform.system() == "Darwin"
CONFIG_FILE = os.path.expanduser("~/focus_guard_config.json")

# 執法名單
HARD_BLACKLIST = [
    "roblox", "minecraft", "steam", "genshin", "shorts", "reels", "tiktok", "netflix",
    "gameplay", "walkthrough", "speedrun", "esports", "league of legends", "valorant", 
    "apex", "pubg", "fortnite", "gta", "grand theft auto", "cyberpunk", "witcher", 
    "zelda", "mario", "pokemon", "pewdiepie", "mrbeast gaming", "markiplier", "ninja", 
    "shroud", "faker", "統神", "國動", "丁特", "史丹利", "toyz", "阿神", "老高", 
    "實況", "精華", "遊戲", "電競", "打機", "攻略", "抽卡", "上分", "lol", 
    "games", "gaming", "azagames"
]

# --- 核心組件 ---

class Enforcer:
    @staticmethod
    def redirect_current_tab(url="https://www.youtube.com"):
        if not IS_MAC: return
        script = f'''
        ignoring application responses
            tell application "Google Chrome" to set URL of active tab of front window to "{url}"
        end ignoring
        '''
        try:
            subprocess.run(["osascript", "-e", script], timeout=3, check=False)
        except Exception as e:
            print(f"[Enforcer] AppleScript 失敗: {e}")

    @staticmethod
    def kill_game_process():
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if any(game in name for game in ["roblox", "minecraft", "steam"]):
                    proc.kill()
                    return True
            except: pass
        return False

class YouTubeAPIManager:
    _cache = {}
    _channel_cache = {}

    @staticmethod
    def extract_video_id(url):
        match = re.search(r'(?:v=|youtu\.be/)([^&?]+)', url)
        return match.group(1) if match else None

    @staticmethod
    def extract_channel_info(url):
        match = re.search(r'youtube\.com/@([^/?&]+)', url)
        if match: return match.group(1), "handle"
        match = re.search(r'youtube\.com/channel/([^/?&]+)', url)
        if match: return match.group(1), "channelId"
        match = re.search(r'youtube\.com/c/([^/?&]+)', url)
        if match: return match.group(1), "username"
        match = re.search(r'youtube\.com/user/([^/?&]+)', url)
        if match: return match.group(1), "username"
        return None, None

    @staticmethod
    def check_video(video_id):
        if video_id in YouTubeAPIManager._cache:
            return YouTubeAPIManager._cache[video_id]
        if not YOUTUBE_API_KEY: return "unknown"
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,topicDetails&id={video_id}&key={YOUTUBE_API_KEY}"
        try:
            r = requests.get(url, timeout=3)
            data = r.json()
            if not data.get("items"): return "unknown"
            
            item = data["items"][0]
            category_id = item.get("snippet", {}).get("categoryId", "")
            topics = item.get("topicDetails", {}).get("topicCategories", [])
            topics_str = " ".join(topics).lower()
            
            # 娛樂判定 (20: Gaming, 24: Entertainment)
            if category_id in ["20", "24"] or any(kw in topics_str for kw in ["game", "esports", "animation"]):
                res = "entertainment"
            elif category_id in ["27", "28"]:
                res = "learning"
            else:
                res = "unknown"
            
            YouTubeAPIManager._cache[video_id] = res
            return res
        except:
            return "unknown"

class AIClassifier:
    @staticmethod
    def classify_content(title, url):
        text = (title + " " + url).lower()
        url_clean = url.split("?")[0].rstrip("/").lower()
        
        # 1. 第一層：關鍵字與 Shorts 阻擋
        if "youtube.com/shorts/" in url.lower() or any(word in text for word in HARD_BLACKLIST):
            return "entertainment"
            
        # 2. 第二層：YouTube 官方 API 精準判定
        if "youtube.com" in url.lower() or "youtu.be" in url.lower():
            vid = YouTubeAPIManager.extract_video_id(url)
            if vid:
                yt_res = YouTubeAPIManager.check_video(vid)
                if yt_res != "unknown": return yt_res
        
        # 3. 第三層：AI 語意判定 (Gemini)
        if not GEMINI_API_KEY: return "learning"
        try:
            payload = {
                "contents": [{"parts": [{"text": f"判斷此內容為 learning, music 或 entertainment (僅回傳單字): {title} {url}"}]}]
            }
            # 使用 Gemini 1.5 Flash
            url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            r = requests.post(url_api, json=payload, timeout=3)
            res = r.json()['candidates'][0]['content']['parts'][0]['text'].strip().lower()
            return "entertainment" if "entertainment" in res else "learning"
        except:
            return "learning"

# --- UI 與邏輯 ---

class FocusGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Guard Pro - 雲端版")
        self.root.geometry("500x650")
        self.root.config(bg="#FDFCFB")
        
        self.is_active = False
        self.student_id = self.load_student_id()
        self.current_remote_status = "UNLOCKED"
        
        tk.Label(root, text="🛡️ Focus Guard Pro", font=("Arial", 22, "bold"), fg="#1A1A2E", bg="#FDFCFB").pack(pady=10)
        
        # 顯示識別代碼
        id_frame = tk.Frame(root, bg="#F0EEF8", padx=20, pady=10)
        id_frame.pack(pady=10)
        tk.Label(id_frame, text="您的遠端識別代碼", font=("Arial", 10), fg="#5A5A72", bg="#F0EEF8").pack()
        tk.Label(id_frame, text=self.student_id, font=("Courier", 24, "bold"), fg="#7B4DC9", bg="#F0EEF8").pack()
        
        self.status_lbl = tk.Label(root, text="狀態：連線中...", font=("Arial", 14), fg="#A0A0B8", bg="#FDFCFB")
        self.status_lbl.pack(pady=5)

        self.log_area = tk.Text(root, height=12, width=50, bg="#F0F0F0", fg="#1A1A2E", font=("Courier", 11))
        self.log_area.pack(pady=10, padx=20)
        self.log(f"✅ 系統啟動，正在與雲端同步...")
        self.log(f"📍 伺服器：{SERVER_URL}")

        # 啟動背景執行緒
        threading.Thread(target=self.cloud_sync_loop, daemon=True).start()
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def load_student_id(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f).get("student_id", "PRO-ERROR")
            except: pass
        
        # 產生新 ID
        new_id = f"PRO-{str(uuid.uuid4())[:4].upper()}"
        with open(CONFIG_FILE, "w") as f:
            json.dump({"student_id": new_id}, f)
        return new_id

    def log(self, msg):
        def _upd():
            ts = time.strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{ts}] {msg}\n")
            self.log_area.see(tk.END)
        self.root.after(0, _upd)

    def cloud_sync_loop(self):
        """ 每 5 秒與伺服器同步一次狀態 """
        while True:
            try:
                # 連向 server_pro.py 提供的新 API
                api_url = f"{SERVER_URL}/get_status?id={self.student_id}"
                r = requests.get(api_url, timeout=5)
                if r.ok:
                    data = r.json()
                    status = data.get("status", "UNLOCKED")
                    
                    if status != self.current_remote_status:
                        self.current_remote_status = status
                        self.handle_status_change(status)
                    
                    self.status_lbl.config(text=f"狀態：雲端連線中 ({status})", fg="#059669")
                else:
                    self.status_lbl.config(text="狀態：伺服器通訊錯誤", fg="#F87171")
            except Exception as e:
                self.status_lbl.config(text="狀態：網路連線失敗", fg="#F87171")
                # self.log(f"⚠️ 同步錯誤: {e}")
            
            time.sleep(5)

    def handle_status_change(self, status):
        if status == "HARD_LOCK" or status.startswith("TIMER"):
            self.log(f"🔒 接收到雲端指令：啟動鎖定 ({status})")
            self.is_active = True
        else:
            self.log(f"✅ 接收到雲端指令：解除鎖定")
            self.is_active = False

    def monitor_loop(self):
        scan_count = 0
        cooldown = 0
        while True:
            try:
                if self.is_active:
                    scan_count += 1
                    Enforcer.kill_game_process()

                    if IS_MAC:
                        if cooldown > 0:
                            cooldown -= 3
                        else:
                            tabs = self.get_tabs()
                            for tab in tabs:
                                res = AIClassifier.classify_content(tab['title'], tab['url'])
                                if res == "entertainment":
                                    self.log(f"🚨 攔截成功！已關閉違規分頁。")
                                    Enforcer.redirect_current_tab()
                                    cooldown = 3
                                    break
            except: pass
            time.sleep(3)

    def get_tabs(self):
        script = 'tell application "Google Chrome" to get (title of active tab of front window) & "|||" & (URL of active tab of front window)'
        try:
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1)
            parts = r.stdout.strip().split("|||")
            if len(parts) >= 2: return [{"title": parts[0], "url": parts[1]}]
        except: pass
        return []

if __name__ == "__main__":
    root = tk.Tk()
    app = FocusGuardApp(root)
    root.mainloop()
