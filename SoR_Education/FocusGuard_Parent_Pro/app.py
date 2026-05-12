import os
import sys
import time
import threading
import platform
import tkinter as tk

# --- 啟動日誌 (除錯用) ---
try:
    with open(os.path.expanduser("~/focus_guard_debug.log"), "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 程式啟動中 (正式版)...\n")
except: pass

import core.config as config
from core.monitor import FocusGuardApp
from server.api_server import run_api_server, set_app_instance

# 嘗試引入鋼琴監控 (如果有的話)
try:
    import numpy as np
    import sounddevice as sd
    from task_engine import DailyTaskManager
except ImportError:
    sd = None

def add_to_startup():
    """ 將程式加入 Windows 開機啟動清單 """
    if config.IS_WINDOWS:
        try:
            import winreg
            app_path = os.path.realpath(sys.executable)
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "FocusGuardPro", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            print(f"[System] 已成功加入 Windows 開機啟動")
        except Exception as e:
            print(f"[System] Windows 啟動設定失敗: {e}")
    elif platform.system() == "Darwin": # macOS
        try:
            app_path = os.path.realpath(sys.executable)
            if ".app/Contents/MacOS/" in app_path:
                # 如果是在 .app 封裝內執行，獲取 .app 的路徑
                app_path = app_path.split(".app/Contents/MacOS/")[0] + ".app"
            
            cmd = f'tell application "System Events" to make login item at end with properties {{path:"{app_path}", name:"FocusGuardPro", hidden:false}}'
            os.system(f"osascript -e '{cmd}' > /dev/null 2>&1")
            print(f"[System] 已嘗試加入 macOS 登入啟動項")
        except Exception as e:
            print(f"[System] macOS 啟動設定失敗: {e}")

# --- 鋼琴監控執行緒 ---
def piano_monitor_loop():
    if not sd:
        print("⚠️ 未安裝 sounddevice，無法啟動鋼琴監控")
        return
    
    print("🎹 鋼琴監控執行緒已啟動")
    threshold = 0.05  # 音量門檻
    chunk_size = 44100  # 1 秒
    
    def callback(indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        if volume_norm > threshold:
            DailyTaskManager.update_piano_time(1)

    try:
        with sd.InputStream(callback=callback, channels=1, samplerate=44100, blocksize=chunk_size):
            while True:
                time.sleep(10)
    except Exception as e:
        print(f"❌ 鋼琴監控異常: {e}")

if __name__ == "__main__":
    add_to_startup()

    # 啟動本地 API Server
    threading.Thread(target=run_api_server, daemon=True).start()
    
    # 啟動鋼琴監控
    threading.Thread(target=piano_monitor_loop, daemon=True).start()
    
    # 啟動 YouTube 採收轉接員 (處理伺服器被擋的影片)
    try:
        from core.harvest_relay import start_harvest_relay
        threading.Thread(target=start_harvest_relay, daemon=True).start()
    except Exception as e:
        print(f"⚠️ 採收轉接員啟動失敗: {e}")

    root = tk.Tk()
    app_instance = FocusGuardApp(root)
    
    # 將實例傳入 API Server 以便操控狀態
    set_app_instance(app_instance)
    
    root.mainloop()
