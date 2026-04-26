#!/usr/bin/env zsh

# 蕭博士 SoR 美語 · 全系統一鍵啟動器
# ---------------------------------------------------------
# 此腳本會啟動 Hub 中樞以及所有後台伺服器 (Focus Pro, Phonics, Studio, YoutubeDB)

BASE_DIR="/Users/gray/Documents/python project"
cd "$BASE_DIR"

echo "🧹 正在清理舊的背景服務，避免 Port 衝突..."
pkill -f "streamlit run"
pkill -f "server.py"
pkill -f "server_pro.py"
pkill -f "app.py"
sleep 2

echo "🚀 準備啟動 SoR 全系列測試伺服器..."

# 1. 啟動 Focus Guard Pro Server (Port 5100)
echo "➡️ [5100] 啟動 Focus Guard Pro 遠端伺服器..."
cd "$BASE_DIR/SoR_Education/FocusGuard_Parent_Pro"
nohup python3 server_pro.py > /tmp/sor_focus_pro.log 2>&1 &

# 2. 啟動 音典系統 API (Port 5055)
echo "➡️ [5055] 啟動 音典系統 (Phonics App)..."
cd "$BASE_DIR/SoR_Education/sor_phonics_app"
nohup python3 server.py > /tmp/sor_phonics.log 2>&1 &

# 3. 啟動 700單 製作室 (Port 8501)
echo "➡️ [8501] 啟動 Vocab 700 製作室 (Studio)..."
cd "$BASE_DIR/SoR_Education/700單"
nohup python3 -m streamlit run sor_studio.py --server.port 8501 --server.headless true > /tmp/sor_studio.log 2>&1 &

# 4. 啟動 YoutubeDB 影片知識庫 (Port 8504)
echo "➡️ [8504] 啟動 影片知識庫 (YoutubeDB)..."
cd "$BASE_DIR/Systems_Data/youtubedb"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
nohup python3 -m streamlit run Home.py --server.port 8504 --server.headless true > /tmp/sor_youtubedb.log 2>&1 &
deactivate 2>/dev/null

# 5. 啟動 SoR 系統中樞 (Port 8600)
echo "➡️ [8600] 啟動 SoR 系統中樞 (Hub)..."
cd "$BASE_DIR"
# Hub 保持在前台顯示，以便使用者查看日誌
python3 -m streamlit run SoR_Hub.py --server.port 8600 --server.headless true &

echo "────────────────────────────────────────"
echo "✨ 所有系統已在背景啟動中！"
echo "🕒 請稍候 5-10 秒讓服務完全載入..."
echo "👉 系統首頁：http://localhost:8600"
echo "────────────────────────────────────────"

sleep 5
open "http://localhost:8600"

echo "保持這個終端機開啟即可。若要停止所有服務，請直接關閉此視窗。"
wait
