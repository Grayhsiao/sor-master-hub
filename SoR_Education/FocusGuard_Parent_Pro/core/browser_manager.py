import os
import subprocess
import time
import requests
import core.config as config

class BrowserManager:
    @staticmethod
    def is_chrome_guarded():
        """檢查 Chrome 是否已在監控模式 (9222 埠口是否有回應)"""
        try:
            r = requests.get("http://127.0.0.1:9222/json/list", timeout=0.5)
            return r.ok
        except:
            return False

    @staticmethod
    def apply_chrome_policies():
        """自動套用 Chrome 系統原則：禁用自動播放"""
        if config.IS_MAC:
            try:
                # 禁用自動播放 (防懸停底層防禦)
                subprocess.run(["defaults", "write", "com.google.Chrome", "DefaultWebMediaPlayerAutoplaySetting", "-int", "2"], check=False)
                print("🛡️ Chrome 策略已更新：禁用自動播放")
            except Exception as e:
                print(f"⚠️ 無法套用 Chrome 策略: {e}")

    @staticmethod
    def launch_guarded_chrome():
        """以守護模式啟動一個獨立的 Chrome 實例 (不需要關閉原本的 Chrome)"""
        if not config.IS_MAC: return False
        
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ext_path = config.ANTI_HOVER_EXT_PATH
        # 使用永久目錄保存登入資訊（孩子只需要登入一次）
        guard_profile = os.path.expanduser("~/.chrome_guard_profile")
        
        if not os.path.exists(chrome_path):
            print(f"❌ 找不到 Chrome: {chrome_path}")
            return False
        
        os.makedirs(guard_profile, exist_ok=True)
        
        # 套用自動播放禁令政策
        BrowserManager.apply_chrome_policies()
        
        print(f"🚀 正在啟動守護版 Chrome (獨立 profile)...")
        cmd = [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--load-extension={ext_path}",
            f"--user-data-dir={guard_profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--new-window",
            "https://www.youtube.com",  # 直接開 YouTube，讓孩子使用這個視窗
        ]
        
        try:
            # 先殺掉舊 Chrome，確保 9222 埠口是乾淨的
            print("🛑 正在清理現有 Chrome 以便進入守護模式...")
            BrowserManager._kill_unguarded_chrome()
            time.sleep(1)
            
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ 守護版 Chrome 啟動指令已送出")
            return True
        except Exception as e:
            print(f"❌ 啟動失敗: {e}")
            return False

    @staticmethod
    def _kill_unguarded_chrome():
        """殺掉所有沒有 --remote-debugging-port 的舊 Chrome 進程 (保留守護版)"""
        try:
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True
            )
            for line in result.stdout.split("\n"):
                if "Google Chrome" not in line: continue
                if "--remote-debugging-port=9222" in line: continue  # 保留守護版
                if "Google Chrome Helper" in line: continue          # 不動 helper
                if "grep" in line: continue
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        subprocess.run(["kill", "-9", pid], capture_output=True)
                        print(f"🛑 關閉舊 Chrome 進程: PID {pid}")
                    except:
                        pass
            print("✅ 舊 Chrome 已清理完畢，只保留守護版視窗")
        except Exception as e:
            print(f"⚠️ 清理失敗: {e}")

if __name__ == "__main__":
    # 測試程式碼
    print(f"Chrome 是否受控: {BrowserManager.is_chrome_guarded()}")
