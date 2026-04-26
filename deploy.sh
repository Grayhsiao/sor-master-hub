#!/bin/bash
set -e
echo "🚀 準備同步到 Hetzner 伺服器 (77.42.94.7) [路徑: /var/www/sor_hub]..."

rsync -avzu --progress \
    --exclude '.git/' \
    --exclude '**/venv/' \
    --exclude '**/.venv/' \
    --exclude '**/__pycache__/' \
    --exclude '**/*.mp4' \
    --exclude '**/*.mp3' \
    --exclude '**/*.pth' \
    --exclude '**/*.bin' \
    --exclude 'Systems_Data/youtubedb/data/downloaded_files/' \
    --exclude 'SoR_Education/History_Rescue/' \
    --exclude 'SoR_Backups/' \
    --exclude '**/*.db' \
    --exclude 'junior_high_king/*.json' \
    ./ root@77.42.94.7:/var/www/sor_hub/

echo "🔄 強制修正路徑並重啟所有服務..."
ssh root@77.42.94.7 "pm2 delete all 2>/dev/null || true; \
    pm2 start /var/www/sor_hub/venv/bin/python3 --name sor-hub --cwd /var/www/sor_hub -- -m streamlit run SoR_Hub.py --server.port 8503 --server.address 0.0.0.0; \
    pm2 start /var/www/sor_hub/venv/bin/python3 --name youtubedb-app --cwd /var/www/sor_hub/Systems_Data/youtubedb -- -m streamlit run Home.py --server.port 8502 --server.baseUrlPath /youtubedb --server.address 0.0.0.0; \
    pm2 start /var/www/sor_hub/venv/bin/python3 --name song-server --cwd /var/www/sor_hub/SoR_Education/song_teaching -- song_server.py; \
    pm2 start /var/www/sor_hub/venv/bin/python3 --name studio --cwd /var/www/sor_hub/SoR_Education/700單 -- -m streamlit run sor_studio.py --server.port 8501 --server.baseUrlPath /studio --server.address 0.0.0.0; \
    pm2 start /var/www/sor_hub/venv/bin/python3 --name focus-pro-server --cwd /var/www/sor_hub/SoR_Education/FocusGuard_Parent_Pro -- server_pro.py; \
    pm2 save"

echo "✅ 大一統遷移與部署成功！請造訪 https://sor14.duckdns.org"
