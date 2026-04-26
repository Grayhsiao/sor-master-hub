# 🏆 Junior High King (國中知識王)

![Cyberpunk Style](https://img.shields.io/badge/Style-Cyberpunk-bc13fe?style=for-the-badge)
![PHP](https://img.shields.io/badge/Backend-PHP-777bb4?style=for-the-badge)
![SQLite](https://img.shields.io/badge/Database-SQLite-003b57?style=for-the-badge)

## 🌟 專案簡介
「國中知識王」是一款專為國中生設計的互動式學習平台。結合了 **AI 語音辨識** 與 **Cyberpunk 遊戲美學**，讓枯燥的學科練習變得像電玩競技一樣有趣。

## 🎮 核心遊戲模式

### 1. ⚡ 語音心算王 (Cyber Math)
- **玩法**：系統會自動生成四則運算題目，並透過語音讀題。
- **特色**：
    - **純語音答題**：完全不需動手，直接說出答案即可辨識。
    - **強化解析**：支援中文數字辨識（如「十二」、「二十五」）。
    - **連擊系統**：連續答對可獲得額外積分與視覺獎勵。
    - **Cyberpunk UI**：具備霓虹燈光效果與電子報警音感。

### 2. 🎵 猜歌特訓 (Song Guessing)
- **玩法**：聆聽一段音樂片段，猜出正確的歌名。
- **特色**：
    - **YouTube 實時截取**：串接 YouTube 播放最真實的音檔。
    - **雙重答題**：支援語音大聲喊出答案，或點選選項進行四選一。

### 3. 📚 全科學科挑戰 (Subject Quiz)
- **玩法**：針對國文、英文、數學、理化等學科進行題庫測驗。
- **特色**：
    - **詳盡解析**：無論答對或答錯，系統都會彈出詳盡的知識點解析。
    - **排行榜競爭**：所有學科的成績都會記錄在總排行榜中。

## 🛠️ 技術架構
- **Frontend**: HTML5, CSS3 (Modern Flexbox/Grid), JavaScript (Vanilla).
- **Backend**: PHP 8.x.
- **Database**: SQLite3 (`quiz.db`, `education.db`).
- **AI Integration**: Web Speech API (SpeechRecognition & Synthesis).
- **Visualization**: Canvas Confetti, FontAwesome 6.

## ⚙️ 系統需求
- **瀏覽器**：強烈建議使用 **Google Chrome** (以便支援 Web Speech API)。
- **硬體**：需具備麥克風輸入權限。
- **環境**：需在支援 PHP 的 Web Server (如 Apache/Nginx) 下執行。

---
*Created by Antigravity for the Chief.*
