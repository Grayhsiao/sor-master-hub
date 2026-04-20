#!/bin/bash
echo "🚀 準備同步到 Hetzner 伺服器 (77.42.94.7)..."
rsync -avzu --progress --exclude '.git/' --exclude 'venv/' --exclude '__pycache__/' ./ gray@77.42.94.7:~/python_project/
echo "🔄 正在重啟伺服器上的 PM2 服務..."
ssh gray@77.42.94.7 "pm2 restart all"
echo "✅ 大一統同步與重啟完成！伺服器已更新為 v1.3。"
