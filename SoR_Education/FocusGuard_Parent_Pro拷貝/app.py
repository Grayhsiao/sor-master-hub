import sys
import os
import time
import json
import uuid
import re
import threading
import subprocess
import platform
import logging
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog
import psutil
import requests

# --- 基礎配置 ---
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"
STATE_FILE = os.path.expanduser("~/focus_pro_state.json")
FIREBASE_URL = "https://studybuddy-a2dcc-default-rtdb.asia-southeast1.firebasedatabase.app/"

# 幽默金句
MEME_QUOTES = [
    "檢測到大腦處於『待機模式』，請立刻切換至『學習模式』！",
    "孩子，放下電腦，立地成佛。功課還在等你。",
    "Andy 娃娃正在盯著你，別想偷偷玩遊戲喔。",
    "這個視窗太誘人了，為了你的前途，我決定把它變不見。",
    "專注 60 分鐘，換來一輩子的智力。這筆交易很划算吧？"
]

# --- 核心邏輯類別 ---

class StateStore:
    """ 負責持久化存儲計時器狀態 (斷電記憶核心) """
    @staticmethod
    def save(data):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except: pass

    @staticmethod
    def load():
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"mode": "NORMAL", "end_time": 0, "pin": "1234", "api_key": ""}

class AIClassifier:
    """ 視窗監控與 AI 判定 (移植自 guard.py) """
    @staticmethod
    def _run_osascript(script):
        if not IS_MAC: return ""
        try:
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
            return r.stdout.strip() if r.returncode == 0 else ""
        except: return ""

    @staticmethod
    def get_tabs():
        if not IS_MAC: return []
        browsers = [
            ("Google Chrome", 'tell application "Google Chrome" to get title of active tab of front window', 'tell application "Google Chrome" to get URL of active tab of front window'),
            ("Safari", 'tell application "Safari" to get name of front document', 'tell application "Safari" to get URL of front document')
        ]
        tabs = []
        for app, t_scr, u_scr in browsers:
            title = AIClassifier._run_osascript(t_scr)
            url = AIClassifier._run_osascript(u_scr)
            if title: tabs.append({"title": title, "url": url, "owner": app})
        return tabs

    @staticmethod
    def classify(title, url, api_key):
        text = (title + url).lower()
        if any(k in text for k in ["shorts", "reels", "tiktok"]): return "entertainment"
        if not api_key: return "safe"
        
        # 呼叫 Gemini
        payload = {"contents": [{"parts": [{"text": f"網頁：{title} {url}\n判斷為 learning, entertainment 或 safe。只需回傳一個字。"}]}]}
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}", json=payload, timeout=5)
            ans = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            return ans if ans in ["learning", "entertainment", "safe"] else "safe"
        except: return "unknown"

# --- UI 組件 ---

class SuperLockScreen(tk.Toplevel):
    """ 幽默鎖屏 (Hard Lock) """
    def __init__(self, parent, pin, quote):
        super().__init__(parent)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.config(bg="black")
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        canvas.create_text(
            self.winfo_screenwidth()/2, self.winfo_screenheight()/2,
            text=f"🛑 已鎖定 🛑\n\n{quote}",
            font=("Arial", 28, "bold"), fill="#4ade80", justify="center"
        )
        
        btn = tk.Button(self, text="家長解鎖", command=lambda: self.ask(pin))
        canvas.create_window(self.winfo_screenwidth()/2, self.winfo_screenheight()*0.8, window=btn)

    def ask(self, correct_pin):
        val = simpledialog.askstring("解鎖", "輸入 PIN 碼:", show="*", parent=self)
        if val == correct_pin: self.destroy()

# --- 主程式 ---

class FocusGuardPro:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # 隱藏主視窗，專業版通常在後台跑
        
        self.state = StateStore.load()
        self.is_locking = False
        self.lock_ui = None
        self.warning_ui = None
        
        # 啟動遠端監聽
        self.classroom_code = "PRO" + str(uuid.getnode())[-4:] # 基於 MAC Address 的唯一碼
        print(f"家長控制代碼: {self.classroom_code}")
        
        self.start_remote_listener()
        self.start_monitor_loop()
        self.check_resume()

    def start_remote_listener(self):
        def listen():
            while True:
                try:
                    r = requests.get(f"{FIREBASE_URL}/classrooms/{self.classroom_code}.json", timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        if data and "status" in data:
                            self.handle_remote_cmd(data["status"])
                except: pass
                time.sleep(5)
        threading.Thread(target=listen, daemon=True).start()

    def handle_remote_cmd(self, status):
        parts = status.split("|")
        cmd = parts[0]
        
        if cmd == "TIMER":
            mins = int(parts[1])
            self.root.after(0, lambda: self.trigger_timer(mins))
        elif cmd == "SET_PIN":
            self.state["pin"] = parts[1]
            StateStore.save(self.state)
        elif cmd == "UNLOCK":
            self.state["end_time"] = 0
            self.state["mode"] = "NORMAL"
            StateStore.save(self.state)
            if self.lock_ui: self.root.after(0, self.lock_ui.destroy)

    def trigger_timer(self, minutes):
        """ 啟動 60 秒緩衝倒數 """
        if self.warning_ui: return
        self.warning_ui = tk.Toplevel(self.root)
        self.warning_ui.attributes("-topmost", True)
        self.warning_ui.geometry("400x200")
        tk.Label(self.warning_ui, text=f"Andy 提醒\n{minutes} 分鐘專注即將開始\n你有 60 秒準備...", font=("Arial", 14)).pack(pady=20)
        
        def commit():
            self.warning_ui.destroy()
            self.warning_ui = None
            self.state["end_time"] = time.time() + (minutes * 60)
            self.state["mode"] = "LOCKED"
            StateStore.save(self.state)
        
        self.root.after(60000, commit)

    def check_resume(self):
        """ 啟動時檢查是否需要恢復計時 """
        if self.state["mode"] == "LOCKED" and self.state["end_time"] > time.time():
            self.log("偵測到未完成的計時，自動恢復鎖定...")
    
    def start_monitor_loop(self):
        def loop():
            while True:
                now = time.time()
                # 判定鎖定狀態
                if self.state["mode"] == "LOCKED" and now < self.state["end_time"]:
                    if not self.lock_ui or not self.lock_ui.winfo_exists():
                        import random
                        self.root.after(0, lambda: setattr(self, 'lock_ui', SuperLockScreen(self.root, self.state["pin"], random.choice(MEME_QUOTES))))
                
                # AI 監控 (如果是 AI 模式)
                # ... (AI 邏輯待擴充) ...
                
                time.sleep(3)
        threading.Thread(target=loop, daemon=True).start()

    def log(self, msg):
        print(f"[{datetime.now()}] {msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FocusGuardPro(root)
    root.mainloop()
