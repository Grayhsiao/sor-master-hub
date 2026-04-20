#!/bin/bash

# 蕭博士 SoR 內容工廠 - 一鍵啟動腳本 (Mac 版)
# ---------------------------------------------------------

# 1. 取得腳本所在的目錄路徑
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "================================================"
echo "🚀 蕭博士 SoR 內容工廠 正在啟動中..."
echo "================================================"

# 2. 檢查是否安裝了 Python 3
if ! command -v python3 &> /dev/null
then
    echo "❌ 錯誤：未偵測到 Python 3。請先安裝 Python。"
    open https://www.python.org/downloads/
    read -p "按任意鍵結束..."
    exit
fi

# 3. 檢查並建立虛擬環境 (避免污染系統環境)
if [ ! -d "venv" ]; then
    echo "📦 第一次執行，正在建立虛擬環境..."
    python3 -m venv venv
fi

# 4. 啟動虛擬環境並安裝依賴
source venv/bin/activate

echo "🛠️ 正在確認依賴組件 (這可能需要一點時間)..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. 檢查 FFmpeg
if ! command -v ffmpeg &> /dev/null
then
    echo "⚠️ 警告：系統未安裝 FFmpeg，音訊提取功能將無法運作。"
    echo "建議安裝：brew install ffmpeg"
fi

# 6. 啟動 Streamlit 系統
echo "✨ 啟動成功！正在打開瀏覽器視窗..."
streamlit run Home.py --server.headless false

# 保持視窗開啟以顯示日誌
read -p "系統執行中，按 Ctrl+C 可停止。視窗關閉前請按 Enter..."
