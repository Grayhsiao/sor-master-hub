# FocusGuard: Firebase 遠端控制台 3 分鐘設定與檢測教學

## 第一部分：如何自己測試目前的網址有沒有效？

目前程式碼中使用的 Firebase 網址是：
`https://studybuddy-a2dcc-default-rtdb.asia-southeast1.firebasedatabase.app/`

要測試它「能不能用」或是「有沒有權限」，最快的兩個檢測方法：

### 方法 1：最簡單的瀏覽器測試法
直接在瀏覽器（Chrome / Safari）的網址列輸入以下網址並按下 Enter：
👉 `https://studybuddy-a2dcc-default-rtdb.asia-southeast1.firebasedatabase.app/.json`
- **如果網頁顯示**：`{ "error": "Permission denied" }` 👉 代表這個資料庫活著，但是權限被鎖住了，老師的控制台沒辦法發送上課指令。
- **如果網頁顯示**：一些大括號 `{ ... }` 裡面有教室代碼或 null 👉 代表完全正常，可以直接用！
- **如果網頁顯示**：`無法連線 / 找不到伺服器` 👉 代表這個資料庫已經被刪除或過期了，必須重新申請。

### 方法 2：使用老師專用面板測試
1. 在您的電腦上，對著 `teacher_dashboard.html` 點擊右鍵 ➜ 使用瀏覽器開啟。
2. 進入網頁後，點擊下方的 **「🔍 測試資料庫連線」** 按鈕。
3. 觀察下方的系統訊息：
   - 顯示 `✅ 連線正常`：代表功能可以正常使用！
   - 顯示 `❌ 錯誤: 401 或 403`：代表沒有權限寫入，功能失效。

---

## 第二部分：如何免費申請一個新的 Firebase（如果舊的不能用了）

如果測試發現舊的網址已經失效或鎖住，身為**行銷與教育專家**，我強烈建議您重新申請一個您自己專屬的，這樣學生資料跟控制權才會 100% 掌握在我們自己手上。

請跟著以下步驟操作（完全免費，大約 3 分鐘）：

### 步驟 1：建立專案
1. 準備一個您的 Google 帳號。
2. 點擊進入 [Firebase 控制台 (Firebase Console)](https://console.firebase.google.com/)。
3. 點擊畫面上的 **「新增專案 (Add project)」**。
4. 專案名稱輸入：`FocusGuard-Class`（或您喜歡的名字），並勾選同意條款，點擊「繼續」。
5. （可選）您可以關閉 Google Analytics 功能以節省設定時間，接著點擊「建立專案」。

### 步驟 2：建立 Realtime Database (即時資料庫)
1. 專案建立完成後進入後台，點擊左側導覽列的 **「建構 (Build)」**，選擇 **「Realtime Database」**。
2. 點擊畫面中央的 **「建立資料庫 (Create Database)」**。
3. 位置選單：請選擇 `asia-southeast1 (新加坡)`（離台灣最近，連線最快），點選「下一步」。
4. 啟動模式：選擇 **「以測試模式啟動 (Start in test mode)」**，然後點擊「啟用」。

### 步驟 3：取得專屬網址並替換
1. 建立完成後，您會看到畫面上方有一個看起來像這樣的網址：
   `https://focusguard-class-default-rtdb.asia-southeast1.firebasedatabase.app/`
2. **這就是您的新控制台網址！** 將它複製起來。
3. 打開 FocusGuard 專案裡的 `main.py`，把原本的 `FIREBASE_URL` 換成這個新網址。
4. 同時打開 `teacher_dashboard.html`，在大約 274 行的地方有 `const FIREBASE_BASE = "..."`，也把網址換成您的新網址。

---

🎉 恭喜！現在 FocusGuard 的雲端遠端控制功能，已經完全掌控在您手上了！
如果有任何一步卡關，請隨時告訴我！
