## 更新日誌與維護備忘錄 - 2026/03/03

1. **連線重構 (Remote Control):** 升級 `requests.get` 為 `requests.Session()` 以優化 Firebase 的 API 呼叫，成功消除因逾時或多次連接造成之系統卡頓。
2. **阻擋黑名單更新:** 為配合線上無干擾情境，將各大瀏覽器加回強制清除範圍。
3. **擴大授權並結合資料庫:**
    * 增加了匿名機制並綁定 MAC 位準檔（學生 ID 與自訂顯示名稱）: `~/.andy_student_name` 以及 `~/.andy_student_id`。
    * 透過 HTTP PATCH，在學生端成功寫入門禁系統登記事實 (`class/TEST101/students/<studentid>`)。
4. **排名與個人化獎勵 (`teacher_dashboard.html`):** 
    * 實作在頁面抓取所有身處同班級連線之同學並排序即時的安迪幣。
    * 按 +50 給特定人時，不全班廣發。而是透過識別單點廣播 (`target`)。只會給指定的同學金幣！
5. **發佈:**
    已採用 PyInstaller 將套件 (`andy_doll.png`) 及程式完成封裝至 `.app` (存於 `/dist` 中可供 Mac 電腦使用)。
