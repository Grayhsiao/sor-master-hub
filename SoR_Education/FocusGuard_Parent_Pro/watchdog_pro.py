import time
import subprocess
import os
import sys
import psutil
import platform

# --- 設定 ---
# 會自動偵測是執行源碼還是打包後的執行檔
if getattr(sys, 'frozen', False):
    # 打包後的路徑
    BUNDLE_DIR = sys._MEIPASS
    MAIN_APP_NAME = "FocusGuardPro" if platform.system() == "Darwin" else "FocusGuardPro.exe"
    MAIN_APP_PATH = os.path.join(os.path.dirname(sys.executable), MAIN_APP_NAME)
else:
    # 開發環境路徑
    MAIN_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

def is_main_app_running():
    """ 檢查主程式是否正在執行 """
    search_target = "app.py" if not getattr(sys, 'frozen', False) else "FocusGuardPro"
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 兼容 Mac (.app) 與 Windows (.exe) 的搜尋邏輯
            if search_target == "app.py":
                if proc.info['cmdline'] and any("app.py" in cmd for cmd in proc.info['cmdline']):
                    return True
            else:
                if search_target in (proc.info['name'] or ""):
                    return True
        except: pass
    return False

def start_main_app():
    """ 啟動主程式 """
    try:
        if MAIN_APP_PATH.endswith(".py"):
            subprocess.Popen([sys.executable, MAIN_APP_PATH])
        else:
            # 打包後的啟動方式 (Mac 使用 open 指令，Win 直接執行)
            if platform.system() == "Darwin":
                subprocess.Popen(["open", MAIN_APP_PATH])
            else:
                subprocess.Popen([MAIN_APP_PATH])
        print(f"[{time.strftime('%H:%M:%S')}] 影子：已喚醒主程式。")
    except Exception as e:
        print(f"啟動失敗: {e}")

if __name__ == "__main__":
    print("-" * 50)
    print("  Focus Guard Pro 影子守護者 (Watchdog) 已就緒")
    print("  監控路徑：", MAIN_APP_PATH)
    print("-" * 50)

    while True:
        if not is_main_app_running():
            start_main_app()
        time.sleep(5) # 每 5 秒巡邏一次
