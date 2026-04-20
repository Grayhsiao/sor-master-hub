"""
意圖偵測守衛 v2.4 — Intent Detection Guard
=============================================
【方案】直接向 Chrome / Safari / Firefox 詢問目前分頁
  - 不需要 debug 模式、不需要 Quartz、不需要 System Events 遍歷
  - 只需在「系統偏好設定 → 隱私權 → 自動化」授權 Terminal 控制瀏覽器（一次性）

使用方式：
  python3 guard.py   （正常開啟 Chrome 即可，不需要特殊啟動）

偵測範圍：
  - Chrome / Safari / Firefox / Microsoft Edge / Brave / Arc 所有分頁
  - Shorts / Reels / TikTok 零容忍（3 秒攔截）
  - YouTube 娛樂、社群媒體
"""

import os
import re
import json
import time
import logging
import threading
import platform
import subprocess
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

IS_MAC     = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

# ─── 預設設定（會存入 config.json） ──────────────────────────────────────────

DEFAULT_CONFIG = {
    "GEMINI_API_KEY": "",
    "PRIORITY_BLACKLIST": [
        "shorts", "reels", "tiktok", "#shorts", "youtube.com/shorts"
    ],
    "ENTERTAINMENT_KEYWORDS": [
        "mv", "official", "gameplay", "開箱", "直播", "遊戲實況",
        "unboxing", "live", "vlog", "music video", "official video",
        "官方頻道", "粉絲團", "reaction",
        "adopt me", "brookhaven", "blox fruits", "tower of hell", "bedwars",
        "murder mystery 2", "piggy", "jailbreak", "arsenal", "pet simulator",
        "roblox", "荒野亂鬥", "game", "games", "遊戲", "傳說對決", "lol",
        "英雄聯盟", "原神", "genshin", "minecraft", "我的世界", "麥塊", "當個創世神",
        "第五人格", "蛋仔派對", "吃雞", "絕地求生", "pubg", "free fire",
        "傳說", "實況", "攻略", "抽卡", "手遊", "闖關", "全明星塔防", "blox fruit"
    ],
    "LEARNING_KEYWORDS": [
        "教學", "原理", "how to", "tutorial", "百科", "課程",
        "講解", "解說", "學習", "物理", "化學", "數學", "英文",
        "入門", "基礎", "理解", "科學", "explain", "lesson",
        "study", "khan academy", "wikipedia", "維基百科"
    ],
    "SOCIAL_MEDIA_DOMAINS": [
        "instagram.com", "facebook.com", "twitter.com", "x.com",
        "dcard.tw", "ptt.cc", "threads.net", "netflix.com"
    ],
    "ALLOWED_CHANNELS": [
        "老高", "李永樂", "ted", "台大", "開放式課程", "papaya", "彭彭", "泛科學"
    ]
}

CONFIG_FILE = "guard_config.json"
config = DEFAULT_CONFIG.copy()

# ─── 日誌設定 ────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="activity.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

def log(msg: str, level: str = "INFO"):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    except Exception:
        pass  # 打包成 .app 隱藏終端機時，print 可能會失敗
    getattr(logging, level.lower(), logging.info)(msg)

def load_or_create_config():
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config.update(loaded)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 讀取設定檔失敗，使用預設值：{e}")
    else:
        # 第一次執行：在 Terminal 直接輸入 API Key (Tkinter 對話框容易當機)
        print("=" * 60)
        print("  🎉 歡迎使用意圖偵測守衛！")
        print("  請貼上您的 Google Gemini API Key（免費申請）。")
        print("  如果尚無金鑰，請直接按 [Enter] 鍵跳過（將使用關鍵字模式）。")
        print("=" * 60)
        user_key = input("👉 請輸入 API Key (或按 Enter 跳過): ")
        
        config["GEMINI_API_KEY"] = user_key.strip()
            
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print(f"\n✅ 設定與黑名單已存入 {CONFIG_FILE}")
            if config["GEMINI_API_KEY"]:
                print("🤖 AI 模式已啟用！")
            time.sleep(1)
        except Exception as e:
            print(f"儲存設定檔失敗：{e}")

# ─── 載入設定 ────────────────────────────────────────────────────────────────
# 啟動時呼叫一次
load_or_create_config()

# ─── 瀏覽器 AppleScript 查詢設定 ─────────────────────────────────────────────
# (app_process_name, title_script, url_script)
BROWSER_SCRIPTS = [
    (
        "Google Chrome",
        'tell application "Google Chrome" to get title of active tab of front window',
        'tell application "Google Chrome" to get URL of active tab of front window',
    ),
    (
        "Safari",
        'tell application "Safari" to get name of front document',
        'tell application "Safari" to get URL of front document',
    ),
    (
        "Firefox",
        'tell application "Firefox" to get name of front window',
        "",
    ),
    (
        "Microsoft Edge",
        'tell application "Microsoft Edge" to get title of active tab of front window',
        'tell application "Microsoft Edge" to get URL of active tab of front window',
    ),
    (
        "Brave Browser",
        'tell application "Brave Browser" to get title of active tab of front window',
        'tell application "Brave Browser" to get URL of active tab of front window',
    ),
    (
        "Arc",
        'tell application "Arc" to get title of active tab of front window',
        'tell application "Arc" to get URL of active tab of front window',
    ),
]

# ─── AppleScript 執行 ────────────────────────────────────────────────────────

def _run_as(script: str, timeout: float = 1.5) -> str:
    """執行 AppleScript，成功回傳結果；失敗或 timeout 回傳空字串。"""
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return ""

# 每個瀏覽器的「是否在執行」快取（5 秒 TTL，減少 osascript 呼叫次數）
_browser_cache: dict[str, tuple[bool, float]] = {}
_CACHE_TTL = 5.0

def _browser_running(app_name: str) -> bool:
    now = time.time()
    cached = _browser_cache.get(app_name)
    if cached and (now - cached[1]) < _CACHE_TTL:
        return cached[0]
    
    try:
        # 使用 pgrep 瞬間找出行程，比 AppleScript 快 100 倍
        res = subprocess.run(["pgrep", "-ix", app_name], capture_output=True, text=True)
        val = bool(res.stdout.strip())
    except:
        val = False
        
    _browser_cache[app_name] = (val, now)
    return val

def get_browser_tabs() -> list[dict]:
    """
    詢問各瀏覽器目前分頁，回傳：
    [{"title": str, "url": str, "owner": str}]
    """
    tabs = []
    for app_name, title_script, url_script in BROWSER_SCRIPTS:
        if not _browser_running(app_name):
            continue
        title = _run_as(title_script)
        url   = _run_as(url_script) if url_script else ""
        if title:
            tabs.append({"title": title, "url": url, "owner": app_name})
    return tabs

# ─── 提醒視窗 ────────────────────────────────────────────────────────────────

def show_alert(message: str):
    """顯示原生 macOS 警示視窗（thread-safe，不需要 tkinter）。"""
    def _show():
        try:
            # 用 osascript display alert — 可在任意執行緒呼叫，完全 thread-safe
            safe_msg = message.replace('"', '\\"').replace('\n', '\\n')
            subprocess.run(
                ["osascript", "-e",
                 f'display alert "⚠️ 意圖偵測守衛" message "{safe_msg}" as warning'],
                capture_output=True, timeout=30,
            )
        except Exception as e:
            log(f"無法顯示提醒視窗：{e}", "ERROR")
    threading.Thread(target=_show, daemon=True).start()

# ─── 攔截動作：導回 YouTube 首頁 ────────────────────────────────────────────────

def redirect_browser(owner: str):
    try:
        if IS_MAC:
            # 將目前的單一分頁導回 YouTube 首頁
            if owner == "Safari":
                script = 'tell application "Safari" to set URL of current tab of window 1 to "https://www.youtube.com"'
            elif owner == "Firefox":
                # Firefox AppleScript 控制網址支援較差，採用熱鍵全選網址列並替換 (Cmd+L)
                script = '''
                tell application "System Events"
                    keystroke "l" using command down
                    delay 0.1
                    keystroke "https://www.youtube.com"
                    keystroke return
                end tell
                '''
            else:
                # Chrome, Edge, Brave, Arc 等 Chromium 家族
                script = f'tell application "{owner}" to set URL of active tab of front window to "https://www.youtube.com"'
                
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            log(f"已強制導回首頁：{owner}")
        elif IS_WINDOWS:
            # Windows 暫時維持關閉視窗，因無法輕易透過指令更改特定瀏覽器的網址
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if owner.lower() in (w.title or "").lower():
                    w.close()
    except Exception as e:
        log(f"導回首頁時發生錯誤：{e}", "WARNING")

# ─── AI 判定（Gemini）────────────────────────────────────────────────────────

_ai_cache: dict[str, str] = {}   # title → "learning" | "entertainment" | "safe"
_ai_failures: dict[str, int] = {}  # title → 連續失敗次數

def _ai_classify(title: str, url: str) -> str | None:
    """
    呼叫 Gemini API 判斷影片意圖。
    回傳 "learning" / "entertainment" / "safe"，失敗回傳 None（由關鍵字接手）。
    """
    if not config.get("GEMINI_API_KEY"):
        return None

    api_key = config["GEMINI_API_KEY"]
    cache_key = title[:120]
    if cache_key in _ai_cache:
        return _ai_cache[cache_key]

    prompt = (
        f'影片標題："{title}"\n'
        f'網址：{url}\n\n'
        '請判斷這個 YouTube 影片對國中生而言是「學習」還是「娛樂」。\n'
        '規則：\n'
        '- 教學、科學、歷史、語言學習、程式設計 → 回答 learning\n'
        '- 任何電動遊戲(Roblox, 荒野亂鬥等)、短影音、搞笑、MV、直播、八卦、實況 → 回答 entertainment\n'
        '- YouTube 首頁、搜尋頁、新分頁 → 回答 safe\n'
        '只回答一個英文單字：learning、entertainment 或 safe，不要其他內容。'
    )

    api_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8, "temperature": 0}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            api_url, data=body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        response = urllib.request.urlopen(req, timeout=5)
        raw_data = response.read().decode("utf-8")
        data = json.loads(raw_data)
        
        try:
            answer = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
        except (KeyError, IndexError):
            # 可能是因為標題觸發了 Google 的安全審查，導致沒有回傳內容
            log(f"API 回傳格式異常或被安全阻擋，交由關鍵字防護接手", "WARNING")
            return None

        if answer not in ("learning", "entertainment", "safe"):
            answer = "safe"
        _ai_cache[cache_key] = answer
        # 成功後清除失敗紀錄
        _ai_failures.pop(cache_key, None)
        log(f"🤖 AI 判定 [{answer}]：{title[:55]}")
        return answer
    except Exception as e:
        fails = _ai_failures.get(cache_key, 0) + 1
        _ai_failures[cache_key] = fails
        if fails >= 3:
            log(f"AI 判定連續失敗 3 次（強制改用關鍵字防護）：{e}", "WARNING")
            _ai_cache[cache_key] = ""   # 儲存空字串，防止對同一個標題瘋狂發送請求 (429)
            return None
        else:
            log(f"AI 連線不穩或忙碌（準備重試 {fails}/3）：{e}", "WARNING")
            return "safe"  # 暫時放行，給 AI 幾次重試機會，避免被關鍵字誤砍

# ─── 意圖判定 ────────────────────────────────────────────────────────────────

def classify_tab(title: str, url: str) -> str:
    text = (title + " " + url).lower()

    # 最高優先：Shorts / Reels / TikTok（不走 AI，直接攔截）
    if any(k in text for k in config["PRIORITY_BLACKLIST"]):
        return "priority"

    # 社群媒體（不走 AI，直接攔截）
    if any(d in text for d in config["SOCIAL_MEDIA_DOMAINS"]):
        return "social"

    # YouTube 頁面
    if "youtube.com" in text or "youtube" in title.lower():
        # 首頁 / 新分頁 / 搜尋頁 → 安全（不送 AI，節省 quota）
        title_clean = re.sub(r'^\(\d+\)\s*', '', title.strip()).lower()
        plain_titles = {"youtube", "新分頁", "new tab", ""}
        if title_clean in plain_titles or url in ("chrome://newtab/", ""):
            return "safe"
            
        # 白名單優待：只要標題包含允許的頻道名稱或字眼，無條件放行 (不需送 AI)
        if config.get("ALLOWED_CHANNELS"):
            if any(k.lower() in text for k in config["ALLOWED_CHANNELS"]):
                return "safe"

        # 嘗試 AI 判定
        ai_result = _ai_classify(title, url)
        if ai_result:
            return ai_result

        # AI 失敗 → 關鍵字 fallback
        has_learning  = any(k in text for k in config["LEARNING_KEYWORDS"])
        has_entertain = any(k in text for k in config["ENTERTAINMENT_KEYWORDS"])
        
        if has_learning and not has_entertain:
            fallback_res = "learning"
        elif has_entertain:
            fallback_res = "entertainment"
        else:
            # 【極致嚴格模式】AI 拒答，且標題沒有出現學習字眼，就預設踢掉 (殺錯不放過)
            fallback_res = "entertainment"
            
        # 關鍵：將 fallback 結果存入 AI 快取，避免每 0.5 秒狂敲被安全阻擋的 API
        _ai_cache[title[:120]] = fallback_res
        return fallback_res

    return "safe"

# ─── 主守衛 ──────────────────────────────────────────────────────────────────

class IntentGuard:
    POLL_INTERVAL   = 0.5
    SHORTS_DEADLINE = 1.0
    COOLDOWN        = 15.0

    def __init__(self):
        self._priority_first_seen: dict[str, float] = {}
        self._cooldown_map:        dict[str, float] = {}

    @staticmethod
    def _key(title: str, url: str) -> str:
        return (title + url).lower()[:100]

    def _in_cooldown(self, key: str) -> bool:
        last = self._cooldown_map.get(key)
        return bool(last and (time.time() - last) < self.COOLDOWN)

    def _set_cooldown(self, key: str):
        self._cooldown_map[key] = time.time()

    def _handle_priority(self, title: str, url: str, owner: str):
        key = self._key(title, url)
        if self._in_cooldown(key):
            return
        log(f"🚫 [零容忍] 即時攔截短影音：{title[:55]}", "WARNING")
        redirect_browser(owner)
        self._set_cooldown(key)

    def _handle_violation(self, title: str, url: str, reason: str, message: str, owner: str):
        key = self._key(title, url)
        if self._in_cooldown(key):
            return
        log(f"⛔ [{reason}] 攔截：{title[:55]}", "WARNING")
        redirect_browser(owner)
        self._set_cooldown(key)

    def scan_once(self):
        if IS_MAC:
            tabs = get_browser_tabs()
        else:
            tabs = []
            try:
                import pygetwindow as gw
                BROWSER_ID = ["chrome","firefox","edge","brave","arc","opera","safari"]
                for w in gw.getAllWindows():
                    t = (w.title or "").strip()
                    if t and any(b in t.lower() for b in BROWSER_ID):
                        tabs.append({"title": t, "url": "", "owner": ""})
            except Exception as e:
                log(f"Windows 視窗讀取錯誤：{e}", "ERROR")

        # 清除已消失分頁的 Shorts 計時器
        current_keys = {self._key(t["title"], t["url"]) for t in tabs}
        for k in list(self._priority_first_seen):
            if k not in current_keys:
                self._priority_first_seen.pop(k, None)

        for tab in tabs:
            title, url, owner = tab["title"], tab["url"], tab["owner"]
            result = classify_tab(title, url)

            if result == "priority":
                self._handle_priority(title, url, owner)
            elif result == "social":
                self._handle_violation(title, url, "社群軟體",
                    "偵測到社群媒體內容，請注意時間！\n回到學習，加油！🎯", owner)
            elif result == "entertainment":
                self._handle_violation(title, url, "YouTube 娛樂",
                    "偵測到非學習內容，請注意時間！\n現在是學習時間 📚", owner)
            elif result == "learning":
                log(f"✅ 學習：{title[:55]}")

    def run(self):
        log("=" * 58)
        log("  意圖偵測守衛 v2.6 — 零延遲模式")
        log(f"  AI 模式：{'✅ 啟用' if config.get('GEMINI_API_KEY') else '❌ 未啟用（使用關鍵字）'}")
        log(f"  設定檔：{CONFIG_FILE}")
        log(f"  偵測頻率：{self.POLL_INTERVAL}s | 短影音：0 秒攔截")
        log(f"  冷卻時間：{self.COOLDOWN}s")
        log("  監控：Chrome / Safari / Firefox / Edge / Brave / Arc")
        log("=" * 58)
        try:
            while True:
                self.scan_once()
                time.sleep(self.POLL_INTERVAL)
        except KeyboardInterrupt:
            log("守衛已手動停止。")

if __name__ == "__main__":
    IntentGuard().run()
