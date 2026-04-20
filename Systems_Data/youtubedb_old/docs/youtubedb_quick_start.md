# 🚀 YouTubeDB 快速上手手冊 (Quick Start Guide)

本手冊提供系統常用操作的標準步驟。

---

## 🎬 情境一：我想採收新的 YouTube 影片
**使用程式：** `import_youtube_batch.py`

1.  **修改目標**：打開 `core/import_youtube_batch.py`，找出第 12 行的 `TARGET_URL`。
2.  **填入網址**：將引號內的網址換成您想抓的「單一影片」或「播放清單」。
3.  **執行採收**：在終端機輸入：
    ```bash
    cd core
    python3 import_youtube_batch.py
    ```
4.  **結果**：程式會自動完成「下載 -> 轉錄 -> AI 分析 -> 建立索引」。

---

## 📂 情境二：我想處理硬碟裡的影片檔
**使用程式：** `process_local_media.py`

1.  **準備檔案**：將影片放入指定的下載資料夾（或修改程式內的路徑）。
2.  **執行處理**：
    ```bash
    python3 process_local_media.py
    ```
    *註：此程式支援大檔案自動分割，不用擔心 25MB 限制。*

---

## 📄 情境三：我手頭有純文字檔 (例如：講義、文章、筆記)
**使用程式：** `import_text_local.py`

1.  **執行命令**：
    ```bash
    python3 import_text_local.py "您的檔案路徑.txt"
    ```
2.  **結果**：程式會自動完成「文字讀取 -> AI 分析 -> 生成 SoR 策略」並將檔案存入 `sources/`。
3.  **索引**：完成後，請記得到 `app.py` 點擊「重建資料庫」，該文章就能被搜尋到。

---

## ✍️ 情境四：我想手動修改/重新生成某影片的 AI 策略
**使用程式：** `refine_strategy_ai.py`

1.  **用途**：如果您覺得之前的 AI 分析不夠好，或是想換模型 (Gemini vs GPT)。
2.  **執行**：
    ```bash
    python3 refine_strategy_ai.py --file YOUR_SRT_FILE.srt
    ```

---

## 📢 情境四：我想產出 Line Flex Message 或社群文案
**使用程式：** `export_marketing_assets.py`

1.  **執行**：
    ```bash
    python3 export_marketing_assets.py
    ```
2.  **結果**：程式會掃描 `sources/` 資料夾中所有的 `_strategy.txt`，並在 `output/` (或指定目錄) 產出對應的 JSON 與草稿。

---

## 🔎 情境五：我想搜尋並觀看採收好的影片
**使用程式：** `app.py`

1.  **啟動介面**：
    ```bash
    streamlit run app.py
    ```
2.  **操作**：在網頁輸入關鍵字，點擊搜尋結果中的文字，即可直接跳轉到 YouTube 對應的時間點播放。

---

## 🩺 疑難排解：系統怪怪的？
執行 `sys_diagnose.py`：
```bash
python3 sys_diagnose.py
```
它會告訴您是哪一個 API Key 沒設好，或是哪一個資料夾不見了。
