# 🛠️ 實用工具技巧 (Tips)

---

## OpenAI Playground — 不用寫程式就能測試提示詞

> 🔗 網址：[https://platform.openai.com/playground](https://platform.openai.com/playground)

**用途**：直接把 `prompts_collection.md` 裡的提示詞貼進去，搭配逐字稿測試，比較哪個版本輸出最好——完全不需要跑任何程式。

| 欄位 | 填什麼 |
|------|--------|
| **System** | 角色設定，如「你是蕭博士的文案助手」 |
| **User** | 提示詞內容 + 逐字稿 |
| **Model** | 選 `gpt-4o` |
| **Temperature** | 0.2 穩定 / 0.7 有創意 |

💡 **最佳使用方式**：開兩個分頁，各貼一個版本，輸入同一段逐字稿，直接肉眼比較結果。

---

## 省錢技巧

- **優先用快取逐字稿**：`utils.get_or_transcribe()` 會自動檢查同名 `.txt` 是否存在，有就跳過 Whisper 呼叫。
- **Gemini 替換 GPT-4o**：`generate_sor_content()` 支援 Gemini 模型，在 Streamlit 介面的設定中可切換。
- **批次採收**：一次給多個 URL，下載後檔案如已存在會自動 skip，不重複下載。

---

## 常見問題排查

### `❌ 請設定環境變數 OPENAI_API_KEY`
確認 `.env` 檔案在 `core/` 資料夾下，且內容格式正確：
```
OPENAI_API_KEY=sk-xxxxxxxx
GOOGLE_API_KEY=AIzaxxxxxxxx
```

### `ModuleNotFoundError: No module named 'chromadb'`
```bash
pip install -r requirements.txt
```

### 向量資料庫查無結果
至「知識庫搜尋」頁面，點擊左側「🔄 重建向量資料庫」按鈕。
