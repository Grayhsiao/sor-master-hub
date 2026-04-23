import time
import subprocess
import os
import sys
import psutil

# 設定主程式路徑
MAIN_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")

def is_process_running(process_name_or_path):
    """ 檢查主程式是否正在執行 """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 檢查進程名稱或是命令列是否包含 main.py
            if proc.info['cmdline'] and any("main.py" in cmd for cmd in proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def start_main_app():
    """ 啟動主程式 """
    print(f"[{time.strftime('%H:%M:%S')}] 哨兵：偵測到主程式已離線，正在重新啟動...")
    subprocess.Popen([sys.executable, MAIN_APP_PATH])

if __name__ == "__main__":
    print("-" * 50)
    print("  Focus Guard 3.0 影子守護者 (Watchdog) 已啟動")
    print("  監控對象：", MAIN_APP_PATH)
    print("-" * 50)
    
    try:
        while True:
            if not is_process_running("main.py"):
                start_main_app()
            time.sleep(5) # 每 5 秒巡邏一次
    except KeyboardInterrupt:
        print("\n影子守護者已關閉。")
