# 🧭 蕭博士影音採收工具 (youtubedb) - 系統手冊

> **專案定位**：影音素材採收、轉錄、深度分析與行銷文案生成。
> **排除項目**：本資料夾「不包含」Line 機器人的運行邏輯。

---

## 🛠️ 三大核心工具

### 1. 影音採收員 (`core/process_local_media.py`)
*   **用途**：處理外接硬碟或本機的長影片。
*   **功能**：自動提取音訊 -> 智能分割 (避開 Whisper 25MB 限制) -> 轉錄 -> 合併。

### 2. 策略文案機 (`core/refine_strategy_ai.py`)
*   **用途**：將轉錄後的逐字稿轉化為 SoR 教學策略。
*   **功能**：調用 Gemini / GPT-4o 生成【理論背景】、【比喻外殼】與【Q&A】。

### 3. 行銷資產引擎 (`core/export_marketing_assets.py`)
*   **用途**：將教學策略轉化為社群貼文。
*   **功能**：一鍵生成 Line Flex Message (JSON)、Threads 貼文、LineOA 廣播稿。

---

## 🚀 網頁展示介面 (`core/app.py`)
*   執行 `streamlit run core/app.py` 啟動。
*   **功能**：跨影片搜尋、即時觀看對應時間點的 YouTube 教學。

---
**維護者**：Antigravity
**更新日期**：2026-02-17
