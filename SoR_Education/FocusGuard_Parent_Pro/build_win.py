import os
import subprocess
import sys
import shutil

# --- 設定 ---
APP_NAME = "FocusGuardPro"
GUARD_NAME = "GuardPro"
DIST_NAME = "FocusGuardPro_Win_Friendly"
VENV_DIR = ".venv"

def run_cmd(cmd):
    """ 強化的執行指令函數，出錯時提供詳細資訊 """
    print(f">> 執行指令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        # 在 Windows 下確保 shell=True 與正確轉義，並捕捉輸出
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout: print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("\n" + "!"*40)
        print(f"❌ 指令執行失敗!")
        print(f"錯誤代碼: {e.returncode}")
        print(f"標準輸出: {e.stdout}")
        print(f"錯誤輸出: {e.stderr}")
        print("!"*40 + "\n")
        raise e

def get_venv_bin(name):
    """ 獲取虛擬環境中的執行檔路徑 (Windows 專用) """
    return os.path.join(VENV_DIR, "Scripts", name)

def main():
    print("="*50)
    print("   Focus Guard Pro 全智慧封裝引擎 (VENV 模式)")
    print("="*50)

    # 1. 建立虛擬環境
    if not os.path.exists(VENV_DIR):
        print(f"📦 正在建構純淨虛擬環境 {VENV_DIR}...")
        run_cmd([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(f"✅ 已偵測到虛擬環境，跳過建構。")

    # 2. 安裝套件到虛擬環境
    venv_python = get_venv_bin("python")
    pip_exe = get_venv_bin("pip")
    print(f"📥 正在虛擬環境中安裝/更新必要套件...")
    if os.path.exists("requirements.txt"):
        run_cmd([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        run_cmd([pip_exe, "install", "-r", "requirements.txt"])
    else:
        run_cmd([pip_exe, "install", "pyinstaller", "psutil", "Pillow", "requests"])

    # 3. 確保圖示存在 (使用虛擬環境的 Python 運行圖示處理)
    if not os.path.exists("icon.ico") and os.path.exists("andy_doll.png"):
        print("🎨 正在生成 Windows 圖示 (.ico)...")
        icon_logic = "from PIL import Image; img = Image.open('andy_doll.png'); img.save('icon.ico', format='ICO', sizes=[(256, 256)])"
        run_cmd([venv_python, "-c", f'"{icon_logic}"'])

    # 4. 執行封裝 (使用虛擬環境內的 PyInstaller)
    pyi_exe = get_venv_bin("pyinstaller")
    
    print(f"🚀 正在封裝主程式 {APP_NAME}...")
    main_cmd = [
        pyi_exe, "--noconsole", "--onefile",
        "--name", APP_NAME,
        "--icon", "icon.ico" if os.path.exists("icon.ico") else "NONE",
        "--add-data", "andy_doll.png;.",
        "app.py"
    ]
    run_cmd(main_cmd)

    print(f"🚀 正在封裝守護者 {GUARD_NAME}...")
    guard_cmd = [
        pyi_exe, "--noconsole", "--onefile",
        "--name", GUARD_NAME,
        "--icon", "icon.ico" if os.path.exists("icon.ico") else "NONE",
        "watchdog_pro.py"
    ]
    run_cmd(guard_cmd)

    # 5. 整理目錄結構
    print("📂 正在整理目錄結構...")
    if os.path.exists(DIST_NAME):
        shutil.rmtree(DIST_NAME)
    os.makedirs(DIST_NAME)
    os.makedirs(os.path.join(DIST_NAME, "Resources"))

    shutil.copy(os.path.join("dist", f"{APP_NAME}.exe"), DIST_NAME)
    shutil.copy(os.path.join("dist", f"{GUARD_NAME}.exe"), os.path.join(DIST_NAME, "Resources"))
    if os.path.exists("README_家長請看我.txt"):
        shutil.copy("README_家長請看我.txt", DIST_NAME)

    print("\n" + "="*50)
    print(f"✅ 建置全數成功！")
    print(f"產出目錄: {DIST_NAME}")
    print("提示: 您可以將此目錄壓縮發佈，家長端不需裝 Python 即可執行。")
    print("="*50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 建置過程中斷: {e}")
        input("按任意鍵確認...")
