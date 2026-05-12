import os
import time
import json
import uuid
import threading
import subprocess
import requests
import psutil
import tkinter as tk
from PIL import Image, ImageTk

import core.config as config
from core.classifier import AIClassifier
from core.enforcer import Enforcer
from core.browser_manager import BrowserManager

# 嘗試主動觸發 Mac 輔助使用權限詢問
if config.IS_MAC:
    try:
        from ctypes import c_bool, c_void_p, c_int, CDLL
        import ctypes.util
        app_services = CDLL(ctypes.util.find_library('ApplicationServices'))
        # AXIsProcessTrustedWithOptions with kAXTrustedCheckOptionPrompt: True
        app_services.AXIsProcessTrustedWithOptions.restype = c_bool
        # 這裡不真的去 call，但確保有載入，或者用簡易 AppleScript 觸發
        os.system('osascript -e "tell application \"System Events\" to get name" > /dev/null 2>&1')
    except: pass

# SoR AI 模組
try:
    from task_engine import FocusState
except ImportError:
    FocusState = None

class FocusGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Guard Pro - 雲端版")
        self.root.geometry("500x650")
        self.root.config(bg="#FDFCFB")
        
        self.is_active = True  # 監控永遠開啟
        self.student_id = self.load_student_id()
        self.current_remote_status = "LOCKED"  # 預設鎖定
        self.cloud_reward_unlocked = False  # 雲端獎勵解鎖（暫時允許 YouTube）
        self.repair_btn_visible = False
        
        # 加入雲端黑名單同步
        threading.Thread(target=self.fetch_cloud_config, daemon=True).start()

        # --- 加入 Andy Doll 圖片 ---
        self.history_file = os.path.expanduser("~/focus_guard_intercept_history.json")
        try:
            img_path = config.resource_path("andy_doll.png")
            if os.path.exists(img_path):
                img_obj = Image.open(img_path)
                # 調整圖片大小以符合介面
                img_obj = img_obj.resize((120, 120), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(img_obj)
                self.img_label = tk.Label(root, image=self.photo, bg="#FDFCFB")
                self.img_label.pack(pady=(20, 0))
        except Exception as e:
            print(f"[UI] 載入圖片失敗: {e}")

        tk.Label(root, text="🛡️ Focus Guard Pro", font=("Arial", 22, "bold"), fg="#1A1A2E", bg="#FDFCFB").pack(pady=10)
        
        # 顯示識別代碼
        id_frame = tk.Frame(root, bg="#F0EEF8", padx=20, pady=10)
        id_frame.pack(pady=10)
        tk.Label(id_frame, text="您的遠端識別代碼", font=("Arial", 10), fg="#5A5A72", bg="#F0EEF8").pack()
        tk.Label(id_frame, text=self.student_id, font=("Courier", 24, "bold"), fg="#7B4DC9", bg="#F0EEF8").pack()
        
        self.status_lbl = tk.Label(root, text="狀態：連線中...", font=("Arial", 14), fg="#A0A0B8", bg="#FDFCFB")
        self.status_lbl.pack(pady=5)

        # --- Chrome 守護狀態橯 (Chrome Guard Status Banner) ---
        self.guard_banner = tk.Frame(root, bg="#FEE2E2", padx=10, pady=8)
        self.guard_banner.pack(fill=tk.X, padx=20, pady=(0, 5))
        self.guard_lbl = tk.Label(self.guard_banner, 
                                  text="⚠️ Chrome 尚未進入守護模式",
                                  font=("Arial", 11), fg="#991B1B", bg="#FEE2E2")
        self.guard_lbl.pack(side=tk.LEFT)
        self.repair_btn = tk.Button(self.guard_banner, text="🚀 一鍵張守", command=self.repair_browser,
                                   bg="#DC2626", fg="white", font=("Arial", 11, "bold"), padx=8)
        self.repair_btn.pack(side=tk.RIGHT)

        self.log_area = tk.Text(root, height=12, width=50, bg="#F0F0F0", fg="#1A1A2E", font=("Courier", 11))
        self.log_area.pack(pady=10, padx=20)
        self.log(f"✅ 系統啟動，正在與雲端同步...")
        self.log(f"📍 伺服器：{config.SERVER_URL}")

        # 啟動背景執行緒
        threading.Thread(target=self.cloud_sync_loop, daemon=True).start()
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        # 立即檢查并更新 Chrome 守護狀態橯
        threading.Thread(target=self._initial_browser_check, daemon=True).start()


    def _initial_browser_check(self):
        """啟動後 2 秒檢查 Chrome，並更新 UI Banner"""
        time.sleep(2)
        is_guarded = BrowserManager.is_chrome_guarded()
        self._update_guard_banner(is_guarded)

    def _update_guard_banner(self, is_guarded):
        def _upd():
            if is_guarded:
                self.guard_banner.config(bg="#D1FAE5")
                self.guard_lbl.config(text="✅ Chrome 守護模式已啟動", fg="#065F46", bg="#D1FAE5")
                self.repair_btn.config(text="🔄 重新套用", bg="#059669")
            else:
                self.guard_banner.config(bg="#FEE2E2")
                self.guard_lbl.config(text="⚠️ Chrome 尚未進入守護模式", fg="#991B1B", bg="#FEE2E2")
                self.repair_btn.config(text="🚀 一鍵張守", bg="#DC2626")
        self.root.after(0, _upd)

    def load_student_id(self):
        if os.path.exists(config.CONFIG_FILE):
            try:
                with open(config.CONFIG_FILE, "r") as f:
                    return json.load(f).get("student_id", "PRO-ERROR")
            except: pass
        
        # 產生新 ID
        new_id = f"PRO-{str(uuid.uuid4())[:4].upper()}"
        with open(config.CONFIG_FILE, "w") as f:
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
                # 忽略 SSL 警告
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                api_url = f"{config.SERVER_URL}/get_status?id={self.student_id}"
                r = requests.get(api_url, timeout=5, verify=False, proxies={"http": None, "https": None})
                if r.ok:
                    data = r.json()
                    # 如果伺服器沒給狀態，預設為 LOCKED (安全第一)
                    status = data.get("status", "LOCKED")
                    
                    if status != self.current_remote_status:
                        self.current_remote_status = status
                        self.handle_status_change(status)
                    
                    # 根據狀態顯示更直覺的文字
                    display_status = "🔒 攔截中" if status != "UNLOCKED" else "🔓 獎勵解鎖中"
                    color = "#059669" if status == "UNLOCKED" else "#1D4ED8"
                    
                    self.status_lbl.config(text=f"守護狀態：{display_status}", fg=color)
                else:
                    self.status_lbl.config(text="狀態：伺服器通訊錯誤", fg="#F87171")
            except Exception as e:
                self.status_lbl.config(text="狀態：網路連線失敗", fg="#F87171")
                self.log(f"⚠️ 同步錯誤: {e}")
            
            time.sleep(5)

    def fetch_cloud_config(self):
        try:
            config_url = f"{config.SERVER_URL}/cloud_config.json"
            r = requests.get(config_url, timeout=5, verify=False)
            if r.ok:
                data = r.json()
                new_list = data.get("blacklist", [])
                if new_list:
                    AIClassifier.update_cloud_blacklist(new_list)
                    print(f"☁️ 雲端配置同步成功，新增了 {len(new_list)} 筆攔截規則")
        except Exception as e:
            print(f"☁️ 雲端配置同步失敗: {e}")

    def handle_status_change(self, status):
        """雲端狀態只控制「獎勵解鎖」，監控永遠運行"""
        if status == "UNLOCKED":
            # 家長允許孩子使用 YouTube（短暫獎勵）
            self.cloud_reward_unlocked = True
            self.log(f"✅ 雲端指令：獎勵解鎖（允許 YouTube）")
        else:
            # HARD_LOCK, TIMER_xx 等：恢復攔截
            self.cloud_reward_unlocked = False
            self.log(f"🔒 雲端指令：啟動攔截 ({status})")

    def repair_browser(self):
        print("🛠️ 觸發修復瀏覽器按鈕...")
        self.log("⚙️ 正在啟動 Chrome 守護模式...")
        self.repair_btn.config(state=tk.DISABLED, text="⏳ 啟動中...")
        
        def _do_repair():
            success = BrowserManager.launch_guarded_chrome()
            time.sleep(6)  # 等 Chrome 啟動完成 (包含強制關閉等待3秒 + 啟動3秒)
            is_now_guarded = BrowserManager.is_chrome_guarded()
            self._update_guard_banner(is_now_guarded)
            if success and is_now_guarded:
                self.log("✅ Chrome 守護模式啟動成功！懸停預覽功能已封鎖。")
            else:
                self.log("❌ 啟動失敗，請確認是否安裝了 Google Chrome")
            self.root.after(0, lambda: self.repair_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=_do_repair, daemon=True).start()

    def save_intercept_history(self, title, url):
        try:
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    history = json.load(f)
            
            history.insert(0, {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "title": title,
                "url": url
            })
            
            with open(self.history_file, "w") as f:
                json.dump(history[:100], f, indent=2, ensure_ascii=False)
        except: pass

    def show_lock_screen(self, reason):
        # 原本在 app.py 的功能，Windows 專用
        pass

    def _setup_persistent_guard(self):
        """等待 Chrome 就緒後，登記持久防懸停腳本"""
        time.sleep(3)
        for attempt in range(5):
            if Enforcer.setup_persistent_anti_hover():
                self.log("🛡️ 防懸停腳本已持久化（重整頁面仍有效）")
                # 同時立即注入到當前分頁
                Enforcer.inject_anti_hover_via_cdp()
                return
            time.sleep(10)  # 每 10 秒重試一次
        self.log("⚠️ 持久腳本登記失敗（請確認守護版 Chrome 已啟動）")

    def monitor_loop(self):
        print(f"🚀 監控執行緒已啟動 (平台: {'Mac' if config.IS_MAC else 'Windows'})")
        
        # 登記持久防懸停腳本（重整頁面仍有效）
        if config.IS_MAC:
            threading.Thread(target=self._setup_persistent_guard, daemon=True).start()


        scan_count = 0
        cooldown = 0
        last_url = ""
        last_res = "learning"
        last_title = ""

        while True:
            try:
                # 判斷是否解鎖
                status = {"is_unlocked": False}
                if FocusState:
                    status = FocusState.get_unlock_status()
                
                scan_count += 1
                
                if scan_count % 10 == 0:
                    reward = status['is_unlocked'] or self.cloud_reward_unlocked
                    print(f"💓 監控中... (奖勵解鎖: {'YES' if reward else 'NO'}, 攔截中: {'NO' if reward else 'YES'})")

                # 如果奖勵解鎖（任務完成或雲端家長允許）就不攔截
                if status["is_unlocked"] or self.cloud_reward_unlocked:
                    time.sleep(1)
                    continue

                # 監控永遠運行
                Enforcer.kill_game_process()

                if cooldown > 0:
                    cooldown -= 1
                else:
                    tabs = self.get_tabs()
                    if not tabs:
                        if scan_count % 30 == 0:
                            # 檢查是否為權限問題
                            if config.IS_MAC:
                                try:
                                    test_script = 'tell application "System Events" to get name of every process'
                                    subprocess.run(["osascript", "-e", test_script], capture_output=True, timeout=1)
                                    self.log("⚠️ 偵測不到分頁 — 請確認瀏覽器已開啟")
                                except:
                                    self.log("🚫 權限受限：請至系統設定開啟「自動化」權限")
                            else:
                                self.log("⚠️ 偵測不到分頁")
                    if tabs:
                        for tab in tabs:
                            tab_key = f"{tab['url']}_{tab['title']}"
                            if tab_key in getattr(self, '_tab_cache', {}):
                                res, reason_str = self._tab_cache[tab_key]
                            else:
                                res, reason_str = AIClassifier.classify_content(tab['title'], tab['url'])
                                if not hasattr(self, '_tab_cache'):
                                    self._tab_cache = {}
                                self._tab_cache[tab_key] = (res, reason_str)
                                # 限制快取大小，避免記憶體洩漏
                                if len(self._tab_cache) > 100:
                                    self._tab_cache.clear()
                                print(f"[{scan_count}] 偵測: {tab['title'][:50]} | 判定: {res} ({reason_str})")

                            # CDP 注入防懸停腳本（每 5 秒一次）
                            if 'youtube.com' in tab.get('url', '') and scan_count % 5 == 0:
                                t_inject = threading.Thread(target=Enforcer.inject_anti_hover_via_cdp)
                                t_inject.daemon = True
                                t_inject.start()

                            if res == "entertainment":
                                print(f"🚨 啟動攔截！原因: {reason_str}")
                                self.log(f"🚫 攔截: {tab['title'][:40]} | {reason_str}")
                                self.save_intercept_history(tab['title'], tab['url'])
                                if config.IS_MAC:
                                    Enforcer.redirect_current_tab(tab_id=tab.get('id'), url="https://www.youtube.com")
                                else:
                                    self.show_lock_screen(f"偵測到娛樂內容: {tab['title']}")
                                cooldown = 1
                                break
                # 2. 定期檢查 Chrome 守護狀態與持久腳本 (每 5 秒)
                if scan_count % 5 == 0:
                    is_guarded = BrowserManager.is_chrome_guarded()
                    self._update_guard_banner(is_guarded)
                    
                    if is_guarded:
                        if not getattr(self, 'persistent_script_ready', False):
                            if Enforcer.setup_persistent_anti_hover():
                                self.persistent_script_ready = True
                                self.log("✅ 持久防懸停腳本已自動同步")
                    else:
                        self.persistent_script_ready = False

            except Exception as e:
                print(f"監控迴圈異常: {e}")
            time.sleep(1.0)

    _browser_running_cache = {"time": 0, "apps": []}
    _MAIN_BROWSERS = {"Google Chrome", "Safari", "Arc", "Firefox", "Brave Browser"}
    _OSASCRIPT = {
        "Google Chrome": '''tell application "Google Chrome"\n    set tabInfo to ""\n    repeat with w in windows\n        try\n            set t to title of active tab of w\n            set u to URL of active tab of w\n            if u is not "" then\n                set tabInfo to t & "|||" & u\n                exit repeat\n            end if\n        end try\n    end repeat\n    return tabInfo\nend tell''',
        "Safari": '''tell application "Safari"\n    set tabInfo to ""\n    repeat with w in windows\n        try\n            set t to name of current tab of w\n            set u to URL of current tab of w\n            if u is not "" then\n                set tabInfo to t & "|||" & u\n                exit repeat\n            end if\n        end try\n    end repeat\n    return tabInfo\nend tell''',
        "Arc": '''tell application "Arc"\n    set tabInfo to ""\n    repeat with w in windows\n        try\n            set t to title of active tab of w\n            set u to URL of active tab of w\n            if u is not "" then\n                set tabInfo to t & "|||" & u\n                exit repeat\n            end if\n        end try\n    end repeat\n    return tabInfo\nend tell''',
    }

    def get_tabs(self):
        if not config.IS_MAC:
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    t = buf.value
                    return [{"title": t, "url": f"https://windows_app/{t}"}]
            except: pass
            return []

        # CDP
        try:
            r = requests.get("http://127.0.0.1:9222/json/list", timeout=0.8)
            if r.ok:
                all_tabs = []
                for tab in r.json():
                    url = tab.get("url", "")
                    if tab.get("type") == "page" and url and not url.startswith("chrome"):
                        all_tabs.append({"title": tab.get("title", ""), "url": url, "browser": "Chrome(CDP)", "id": tab.get("id", "")})
                if all_tabs:
                    return all_tabs
        except: pass

        # AppleScript
        now = time.time()
        if now - self._browser_running_cache["time"] > 5:
            found = set()
            for proc in psutil.process_iter(['name']):
                try:
                    n = proc.info['name']
                    if n in self._MAIN_BROWSERS:
                        found.add(n)
                except: pass
            self._browser_running_cache = {"time": now, "apps": list(found)}

        for app in self._browser_running_cache["apps"]:
            script = self._OSASCRIPT.get(app)
            if not script:
                continue
            try:
                r = subprocess.run(["osascript", "-e", script],
                                   capture_output=True, text=True, timeout=3)
                if r.returncode == 0 and "|||" in r.stdout:
                    parts = r.stdout.strip().split("|||")
                    return [{"title": parts[0], "url": parts[1], "browser": app}]
            except: pass
        return []
