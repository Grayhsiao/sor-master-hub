# 🛡️ Focus Guard Pro 專案繼承與啟動手冊 (防丟失專區)

> [!IMPORTANT]
> **如果您發現聊天紀錄不見了，請不要慌張！**
> 只要這份檔案還在您的硬碟裡，任何一個 AI 助理都能透過讀取它來「繼承」所有開發脈絡。

## 📍 目前進度：通用發布階段 (VENV 重構)
*   **地端核心**：AI 判讀 + 斷電記憶 + 影子守護已完工 (`app.py`, `watchdog_pro.py`)。
*   **連線修復**：`server_pro.py` (Port 5100) 已上線，修復了 Hub 點擊連結失敗的問題。
*   **Windows 打包引擎**：已完成穩定版重構 (`build_win.py`)，使用 **虛擬環境 (VENV)** 來確保全電腦相容。
*   **家長傳送門**：`portal_pro.html` 已具備遠端 PIN 碼修改與計時功能。

## 🔧 技術架構核心摘要
1.  **影子互保**：主程式與 `GuardPro` 互相監控進程，確保殺不掉。
2.  **遠端遙控**：使用 Firebase Realtime Database (`classrooms` 節點)，透過 `Status` 指令進行同步。
3.  **通用封裝**：使用 `sys.executable -m PyInstaller` 確保 Windows 環境路徑沒設好也能打包。

## 🚀 重啟/換帳號後的「恢復指令」
若您發現紀錄遺失，請直接將此段字複製貼給 AI：
> 「請讀取 `/SoR_Education/FocusGuard_Parent_Pro/PROJECT_HANDOVER_SNAPSHOT.md`。我正在進行 Focus Guard Pro 專案。目前正處於 Windows 封裝驗證階段。請幫我分析 `build_win.py` 並繼續指導我在 Windows 上生成萬用執行檔。」

---
*存檔日期：2026-04-22*
*對話 ID 參考：3d3436fa-4061-43ed-a5d5-22ae3bf04146*
