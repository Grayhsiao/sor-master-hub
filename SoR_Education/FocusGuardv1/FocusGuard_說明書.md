# FocusGuard (Andy Doll Focus) 系統說明書與檢測報告

撰寫人：AI 資深開發 / 蕭博士美語資深行銷與教育顧問

## 一、專案總覽 (Project Overview)
**FocusGuard**（又稱 Andy Doll Focus / SOR Study Buddy）是一款專為學生設計的「專注力輔助工具」。它的核心目的是在學生學習（如上線上課程、寫作業）期間，自動阻擋容易讓人分心的應用程式（如 Minecraft、Roblox、Discord 等遊戲與通訊軟體）。

本系統結合了**蕭博士美語**的教育理念，不只是一個冷冰冰的限制工具，更融入了「安迪娃娃 (Andy Doll)」的視覺形象，並且提供了「遠端教室模式」，讓老師能透過網頁儀表板同步管理全班的專注狀態。

---

## 二、核心功能 (Core Features)

1. **個人專注計時器模式 (Timer Mode)**
   - 學生可自行設定專注時間（預設 30 分鐘）。
   - 啟動後，系統會在背景每 3 秒自動掃描並關閉「黑名單 (Blacklist)」中的應用程式。
   - 支援緊急解鎖機制（預設 PIN 碼：`1234`）。

2. **遠端教室模式 (Classroom Mode)**
   - 學生輸入專屬的「教室代碼（如：ENG101）」即可連線至雲端教室。
   - 系統依據 Firebase 資料庫的狀態，判斷是否進入「鎖定（專注）」或「解鎖（下課）」狀態。

3. **老師專業控制面板 (Teacher Dashboard)**
   - 老師透過 `teacher_dashboard.html` 網頁端。
   - 可一鍵「啟動鎖定 (LOCKED)」或「解除鎖定 (UNLOCKED)」。
   - 介面具備現代感與科技感，提升老師的操作體驗。

4. **防護機制**
   - 嘗試移除傳統的視窗標題列（避免學生輕易按下 X 關閉）。
   - 設有「物理電燈開關」作為彩蛋與關閉按鈕，嘗試關閉時會要求輸入密碼。
   - 記錄使用者的中斷與完成行為至本機端的 Log 檔案 (`focus_activity.log`) 中。

---

## 三、程式碼架構與技術剖析

- **前端與主程式 (`main.py`)**: 
  - 使用 `Tkinter` 開發 GUI 介面。
  - 使用 `PIL (Pillow)` 處理透明背景與圖片縮放。
  - 使用 `psutil` 監控並強制結束 (Kill) 系統中運行的程序 (Processes)。
  - 多執行緒 (`threading`)：分離背景監控程序與 UI 主執行緒，避免介面卡頓。
- **雲端連線 (`remote_control.py`)**: 
  - 使用 `requests` 套件，每 5 秒輪詢 (Polling) Firebase Realtime Database，獲取教室狀態。
- **教師面板 (`teacher_dashboard.html`)**: 
  - 純前端網頁 (HTML/CSS/JS)，直接使用 Firebase REST API (`PATCH` 方法) 更新資料庫狀態。

---

## 四、當前程式碼的問題與隱患 (Code Issues & Risks)

身為您的技術專家，我幫您掃描了程式碼，列出以下幾個需要注意及日後優化的問題：

### 1. 效能與架構隱患
- **低效的 API 輪詢機制 (`remote_control.py`)**：目前是用 `while True` 每 5 秒不斷發送 HTTP Request 到 Firebase。不僅浪費網路資源，如果學生數量多，可能會超過 Firebase 免費額度。**建議**改用 Firebase 官方的 Python SDK (`firebase-admin` 或 `pyrebase`) 的 Realtime Listener，透過 WebSocket 建立長連線。
- **UI 元件管理**：`main.py` 中的 `clear_canvas_widgets` 是透過手動追蹤 `widgets_to_destroy` 陣列來刪除，這種寫法雖然現階段可行，但稍有不慎就容易發生記憶體流失 (Memory Leak) 或畫面重疊殘留。

### 2. 封鎖邏輯 (Blacklist) 太過粗暴
- 目前的封鎖是用「**字串包含 (in)**」來判斷。例如 `BLACKLIST` 中有 `"java"`，只要檔名包含 java（像是 `javascript_ide.exe` 或其他系統必須程式）通通會被誤殺。
- Safari 和 Chrome 目前被列在註解或測試名單中。做為美語線上課程，若學生需要用瀏覽器上課，這部分邏輯需要更精確的「白名單」或「正則表達式 (Regex)」匹配。

### 3. 安全性與權限問題
- **寫死的配置 (Hardcoded Values)**：PIN 碼 (`PIN_CODE = "1234"`) 和 Firebase 通訊網址都直接寫明在 `main.py` 裡。懂得看原始碼的學生能夠輕易破解。
- **Mac 權限問題**：在 macOS 上，強制中止其他軟體的程序通常需要更高的權限 (sudo)，一般使用者權限下 `proc.kill()` 可能會拋出 `AccessDenied`，導致軟體無法真正發揮阻擋遊戲的作用。

### 4. 教師後台的安全審驗
- `teacher_dashboard.html` 使用的是無驗證的 REST API 請求 (`PATCH`)。只要有人知道網址跟教室代碼，就能自己發送 Request 解鎖。雖然有預留 `admin_key` 欄位，但目前只是把值傳上去，並沒有在前端看到加密或登入機制（這依賴您的 Firebase Security Rules 設定是否完善）。

---

## 五、下一步的行銷與優化建議 (行銷與教育觀點)

從**蕭博士美語**的行銷與教學角度來看，這個產品非常有潛力成爲我們課程的「強力附屬服務」，甚至能成為家長買單的理由之一：**「我們不僅教英文，還幫您管理孩子的學習專注力！」**

**建議的下一步發展：**
1. **與 LINE OA 整合**：我們可以加入 LINE 通知功能。當孩子嘗試「輸入錯誤密碼解鎖」或「提早結束專注」時，透過 LINE Bot 發送通知到家長或老師的手機上（「⚠️ 您的孩子 Andy 正在嘗試解除專注模式！」）。這對家長來說是個超級痛點解決方案！
2. **白名單模式**：與其「防堵」遊戲（黑名單抓不勝抓），不如改成「只允許」特定學習軟體（如我們的視訊軟體、電子書）。
3. **獎勵機制**：累積「有效專注時數」後，可以在 APP 內解鎖特定的「安迪娃娃造型」或獲得點數，提高孩子的自主防護意願，達到遊戲化學習的目標。

---
本說明書已準備完成，您可以隨時查閱。若需要開始針對上述問題進行修改（例如更新 Firebase 連線方式、強化防護邏輯，或串接 LINE OA），請隨時告訴我！

## 2026/03/03 重構進展 (Refactoring Progress) 
在本次對話中我們實現了「無延遲遠端更新 (Requests Session)」、修正了 Mac GUI 輸入框 Bug、建立並綁定了帶有儲存狀態的分數機制以及線上學員排行榜並利用 Firebase 的 PATCH 達到了更高效的即時連線。系統已經能由老師網頁端針對個人的專屬 UUID 定點派發金幣給學生（會保存記錄），並順利完成打包了可以脫離 Python 原生環境執行之 Mac App (存放於 dist/)。
---

