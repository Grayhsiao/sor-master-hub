#!/bin/bash
# 蕭博士 SoR 美語 · 系統中樞啟動器
cd "/Users/gray/Documents/python project/Systems_Data/youtubedb"
source venv/bin/activate
echo "✅ 環境載入完成，正在啟動 SoR Hub..."
streamlit run "/Users/gray/Documents/python project/SoR_Hub.py" --server.port 8600
