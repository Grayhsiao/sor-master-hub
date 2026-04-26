#!/usr/bin/env zsh
source ~/.zshrc 2>/dev/null

echo "🧹 正在清理舊的背景服務，避免 Port 打架..."
pkill -f "streamlit run"
pkill -f "server.py"
pkill -f "app.py"
sleep 2

echo "🚀 準備啟動 SoR 全系列本地測試伺服器..."
cd "/Users/gray/Documents/python_project"

# 1. 啟動 SoR 系統中樞 (Port 8600)
echo "➡️ 啟動 系統中樞 (Hub) [Port: 8600]..."
python3 -m streamlit run SoR_Hub.py --server.port 8600 &
sleep 2

# 2. 啟動 Vocab 700 製作室 (Port 8501)
echo "➡️ 啟動 Vocab 700 製作室 (Studio) [Port: 8501]..."
cd "SoR_Education/Vocab_700"
python3 -m streamlit run sor_studio.py --server.port 8501 &
cd ../..
sleep 2

# 3. 啟動 音典系統 API (Port 5055)
echo "➡️ 啟動 音典系統 (Phonics App) [Port: 5055]..."
cd "SoR_Education/sor_phonics_app"
python3 server.py &
cd ../..
sleep 2

# 4. 啟動 YoutubeDB 影片知識庫 (Port 8504)
echo "➡️ 啟動 影片知識庫 (YoutubeDB) [Port: 8504]..."
cd "Systems_Data/youtubedb"
python3 -m streamlit run Home.py --server.port 8504 &
cd ../..
sleep 2

# 5. 啟動 LineBot (Port 5005)
echo "➡️ 啟動 Line 機器人 (LineBot) [Port: 5005]..."
cd "SoR_Education/sor_line_db_bot"
python3 app.py &
cd ../..

echo "────────────────────────────────────────"
echo "✅ 所有系統已在背景啟動完成！"
echo "👉 請開啟中樞面板：http://localhost:8600"
echo "────────────────────────────────────────"
echo "保持這個終端機開啟，如果不要用了直接把視窗關掉即可。"

# 使用 wait 讓視窗不會自動關閉
wait
