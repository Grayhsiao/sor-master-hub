#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "================================================="
echo " Beauty Mask Pro - 終極相容啟動器 (自動環境修復)"
echo "================================================="

# 檢查是否需要安裝 Python 3.10 (Mediapipe 最佳相容版本)
NEED_PYTHON_310=false
if command -v python3 &> /dev/null; then
    # 取得 Python 版本號 (例如 3.13)
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    
    # 判斷版本是否大於等於 3.12 (Mediapipe 目前在此版本容易出錯)
    if [[ $(echo "$PY_VER >= 3.12" | bc -l) -eq 1 ]]; then
        echo "⚠️ 偵測到目前 Python 版本太新 ($PY_VER)！不相容美顏 AI 引擎。"
        NEED_PYTHON_310=true
    fi
else
    echo "⚠️ 找不到 Python 環境！"
    NEED_PYTHON_310=true
fi

# 如果需要，自動下載並安裝 Python 3.10
if [ "$NEED_PYTHON_310" = true ]; then
    echo "🔄 正在自動下載最適合的 Python 3.10 引擎...(這只需安裝一次)"
    # 根據 CPU 架構選擇安裝包 (M1 or Intel)
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        PKG_URL="https://www.python.org/ftp/python/3.10.11/python-3.10.11-macos11.pkg"
    else
        PKG_URL="https://www.python.org/ftp/python/3.10.11/python-3.10.11-macos11.pkg"
    fi
    
    curl -o "/tmp/python3.10.pkg" "$PKG_URL"
    echo "📦 正在為您安裝，可能會要求輸入電腦開機密碼..."
    sudo installer -pkg "/tmp/python3.10.pkg" -target /
    
    # 安裝完畢後更新當前 session 的環境變數
    export PATH="/Library/Frameworks/Python.framework/Versions/3.10/bin:$PATH"
fi

# 決定要使用的 Python 執行檔路徑 (優先使用剛裝好的 3.10)
PYTHON_CMD="python3"
if [ -x "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3" ]; then
    PYTHON_CMD="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
fi

echo "✅ 使用核心大腦: $($PYTHON_CMD --version)"

# 建立獨立的虛擬環境 (防止弄髒 Mac 系統)
if [ ! -d "venv" ]; then
    echo "🏗️ 正在建立專屬空間..."
    $PYTHON_CMD -m venv venv
fi

# 進入虛擬環境
source venv/bin/activate

echo "🔄 正在更新必要套件並下載美顏模型 (約需1-2分鐘)..."
pip install --upgrade pip > /dev/null 2>&1
# 強制指定 mediapipe 版本以避開最新版的雷區
pip install streamlit opencv-python "mediapipe<0.10.10" numpy pillow pyvirtualcam > /dev/null 2>&1

echo "====================================="
echo "🎉 準備就緒！正在開啟 Beauty Mask Pro"
echo "====================================="
echo "請勿關閉這個黑色視窗，網頁即將在您的瀏覽器彈出..."

# 啟動並放在背景
streamlit run live_app.py --server.port 8503 --server.headless true --browser.gatherUsageStats false &
ST_PID=$!

# 等待 4 秒後打開瀏覽器
sleep 4
open "http://localhost:8503"

# 腳本結束時關閉伺服器
wait $ST_PID
