# 🏭 蕭博士內容工廠 (YouTubeDB)

歡迎來到「蕭博士內容工廠」的中央指揮中心。本專案致力於將蕭博士豐富的影音與文字觀念，轉化為 Line OA Bot 與高品質教材的知識庫。

## 🏗️ 系統架構 (Four Zones)

1.  **📥 採收與匯入組 (Ingest Zone)**
    *   處理 YouTube 播放清單、本端媒體檔案。
    *   **核心工具**: `core/import_fb_scraper.py` (FB 智慧採收 - [新版自動化])
    *   **網頁介面**: `pages/5_📱_FB採收.py` (整合 Cookie 儲存與全自動捲動)
2.  **🧠 核心精煉組 (Refinery Zone)**
    *   負責 Whisper 轉錄與 AI 觀念降維。
    *   **核心工具**: `core/content_refinery.py` (SoR 觀念精煉主腦)
3.  **🛠️ 工具與診斷組 (Support Zone)**
    *   影音裁切、社群文案產出、系統狀態診斷。
4.  **🖥️ 指揮中心 (UI Zone)**
    *   由 Streamlit 驅動的數據管理後台 (`Home.py`)。

---

## 📚 快速上手文件 (Documentation)

我們採用分層文件標準，確保所有工具皆有跡可循：

*   **[📖 腳本說明手冊](file:///Users/gray/Documents/python%20project/Systems_Data/youtubedb/docs/SCRIPTS_MANUAL.md)**: 這裡記錄了所有獨立腳本（如 FB 採收器）的安裝與操作流程。
*   **[⚡ 快速啟動](file:///Users/gray/Documents/python%20project/Systems_Data/youtubedb/Home.py)**: 執行 `streamlit run Home.py` 開啟視覺化後台。

---

## 📜 開發規則
1.  **文件先行**: 所有新開發的腳本必須在 `docs/SCRIPTS_MANUAL.md` 同步更新說明。
2.  **分流處理**: 對於大規模採收（如 FB），應先進行內容過濾（精確 vs 隔離），確保資料品質。
3.  **追蹤溯源**: 每個條目都必須標註原始來源（日期、連結或影片名稱）。
