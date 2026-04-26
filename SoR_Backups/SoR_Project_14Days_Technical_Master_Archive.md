# 🛡️ SoR 專案：14 天技術精華大彙整 (2026-04-07 ~ 2026-04-22)

> [!IMPORTANT]
> 本檔案是您這段時間所有開發心血的總結。即使對話消失，此檔案能助您瞬間找回所有專案的技術脈絡。

---

## 🏗️ 核心專案導覽

### 1. Focus Guard Pro (家長專業版)
- **最新狀態**: VENV 智慧封裝腳本已就緒，具備 AI 審查與影子守護。
- **關鍵路徑**: `/SoR_Education/FocusGuard_Parent_Pro/`
- **技術重點**: 使用 `build_win.py` 進行虛擬環境隔離建置，確保 Windows 通用性。

### 2. SoR Vocabulary Studio (700單)
- **最新狀態**: 已導入「單行優先」佈局引擎 (V6.1)，整合 vocab700 正確音調。
- **關鍵路徑**: `/SoR_Education/700單/`
- **技術重點**: 修復音調符號對齊問題，支援自動產出教學影片。

### 3. SoR Phonics App (字典介面)
- **最新狀態**: 完善了七步教學法的排版，精準控制音標與字母的間距。
- **技術重點**: 使用 CSS Grid/Flexbox 鎖定垂直位置，防止頁面跳動。

### 4. SoR Master Hub (系統門戶)
- **最新狀態**: 轉型為企業級 Server Portal，整合所有 AI 服務連結。
- **技術重點**: 修改 `SoR_Hub.py` 將地端工具與雲端 Endpoint 統一管理。

### 5. SoR AI Line Bot
- **最新狀態**: 具備對話記憶功能，優化了向量數據庫索引速度。
- **關鍵路徑**: `/SoR_Education/sor_line_db_bot/`

---

## 🚨 數據救援與恢復 (Google Keep 參考區)

**如果您發現對話不見了，請按照以下步驟操作：**

1. 啟動新的對話。
2. 貼上這段話給 AI：
   > 「我是 Gray，請讀取目錄下 `/SoR_Backups/SoR_Project_14Days_Technical_Master_Archive.md`。我需要接續 [請填入專案名稱，例如：Focus Guard Pro] 的開發。請根據文件中的技術重點，分析代碼並告訴我目前可以進行的下一步。」
3. AI 將會立刻恢復相關的神經網路背景，不必重新解釋需求。

---
*存檔建立日期：2026-04-22*
