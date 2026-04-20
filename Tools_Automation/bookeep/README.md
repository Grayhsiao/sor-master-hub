# 🌸 Bookeep - AI 智慧記帳 & 發票管家

這是一個基於 LINE Messaging API、Google Gemini AI 與 Google Sheets 的全能智慧理財方案。它能理解語音、辨識收據、自動對獎，並提供專業的預算監控報表。

---

## ✨ 核心亮點功能

### 1. 🎫 自動發票對獎 (新功能!)
*   **即時對獎**：拍下發票時，AI 會自動辨識號碼並立即檢查是否中獎。
*   **開獎推播**：尚未開獎的發票會存入系統，並在開獎日（單數月 25-27 號）由機器人自動巡邏並推播中獎喜訊。

### 2. 📊 預算與詳細報表
*   **預算進度條**：報表頂部會顯示預算使用率，超支時進度條會變為紅色。
*   **互動式分類**：點擊報表中的分類按鈕（例如「早餐」），可直接查看該項目的所有消費細目。

### 3. 信用卡帳單批次處理
*   支援上傳信用卡 PDF 帳單或長圖截圖，AI 會自動拆分每一筆消費並顯示彙總。

---

## 🚀 租戶/開發者維護指南 (重要!)

若未來你想要修改機器人的運作方式，請參考以下對照表：

### 💰 如何修改「每月預算」？
*   **雲端修改 (推薦)**：在 Render 的 **Environment Variables** 新增或修改 `MONTHLY_BUDGET` (例如設定為 `8000`)。
*   **程式碼修改**：檔案 `config.py` 中的 `MONTHLY_BUDGET` 變數。

### ⏰ 如何修改「對獎頻率」？
*   **修改位置**：`app.py` 底部。
*   **說明**：目前設定為單數月的 25~27 號下午 4 點執行。若想改回每天檢查，請將 `trigger='cron'` 的參數改回 `hour=2, minute=0`。

### 👨‍👩‍👧 如何管理「家庭成員」？
*   **修改位置**：Render 環境變數 `FAMILY_USER_IDS`。
*   **格式**：多個 ID 請以英文字母逗號 `,` 隔開。

---

## 📂 檔案結構導覽

*   `app.py`: **系統大腦**。處理 LINE 訊息、排程任務與路由。
*   `line_handler.py`: **視覺設計師**。負責設計所有卡片 (Flex Message) 的外觀與按鈕。
*   `gsheet_manager.py`: **資料庫管家**。負責讀寫 Google Sheets 與計算報表。
*   `gemini_manager.py`: **AI 辨識引擎**。定義了 AI 如何看懂你的圖片與文字。
*   `prize_manager.py`: **對獎專家**。負責爬取財政部號碼並執行對獎邏輯。

---

## 🛠 雲端設定 (.env / Render)

| 變數名稱 | 說明 |
| :--- | :--- |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 訊息通訊密鑰 |
| `LINE_CHANNEL_SECRET` | LINE 頻道密鑰 |
| `GOOGLE_SHEETS_ID` | Google 試算表的網址 ID |
| `MONTHLY_BUDGET` | 每月預算金額 (預設 5000) |
| `FAMILY_USER_IDS` | 家庭成員 User ID 清單 |

---

## 👨‍💻 部署與執行
1. **本地測試**：`python3 app.py` (需搭配 ngrok)。
2. **正式發佈**：推送到 GitHub 自動觸發 Render 部署。
3. **選單更新**：修改 `setup_rich_menu.py` 後執行 `python3 setup_rich_menu.py`。

祝你財務健康，發票次次中大獎！🌸💰✨🏆
