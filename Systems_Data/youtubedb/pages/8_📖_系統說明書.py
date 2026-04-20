import streamlit as st

st.set_page_config(
    page_title="系統說明書",
    page_icon="📖",
    layout="wide"
)

st.title("📖 蕭博士 SoR 內容工廠 - 系統說明書")
st.markdown("本頁面提供完整的系統操作流程與底層架構說明，無論您是負責產出內容的行銷人員，還是負責接手維護的開發者，都能在此找到所需資訊。")

tab_user, tab_dev = st.tabs(["🧑‍💻 使用者操作指南 (功能詳解)", "🛠️ 開發者技術文件 (系統架構)"])

with tab_user:
    st.markdown("""
    ## 🔄 核心工作流程總覽
    本系統的主要職責是將「長篇影音資訊」轉換為「易於搜尋的知識庫」與「高轉換率的行銷素材」。
    整體流程為：**採收 (Harvest) ➔ 轉錄 (Transcribe) ➔ 索引 (Index) ➔ 檢索 (Search) / 精煉 (Refine) ➔ 發布 (Publish)**。

    ---

    ## 1. 🎬 採收與轉錄：如何把影片變成知識？
    無論是 YouTube 或是自己拍攝的影片，都需要經過「採收」才能進入系統。
    """)

    with st.expander("🎬 YouTube 採收 (頁面 1) & 📁 本地影片處理 (頁面 6)", expanded=False):
        st.markdown("""
        - **操作邏輯**：
          使用者在介面貼入 YouTube 網址（可一次貼多個，或是貼播放清單），系統會在背後呼叫 `yt-dlp` 下載音訊檔。如果是本地影片，則是直接讀取你的 `.mp4` 檔案。
        - **Whisper 逐字稿生成**：
          影片下載後，系統會自動呼叫 OpenAI 的 **Whisper-1** 模型，將人聲轉換成純文字的 `.srt` 字幕檔，並儲存到 `data/` 資料夾下。
        - **順便自動生成文案**：
          你可以勾選「自動生成 SoR 策略文案」。當逐字稿一產生完畢，系統會**自動去「⚙️ Prompt 管理」裡抓取你設定的「預設 Prompt」**，並呼叫你指定的 AI 模型（如 GPT-4o），直接幫這支影片寫出一篇熱騰騰的行銷文章。
        """)
        
    with st.expander("📱 Facebook 採收 (頁面 7)", expanded=False):
        st.markdown("""
        - **操作邏輯**：此功能用於捕捉競爭對手或自家粉專的貼文素材。
        - **運行方式**：開啟後系統會啟動一個真實的 Chrome 瀏覽器。你需要手動登入 FB，然後畫面會自動往下滾動，將看到的所有貼文文字儲存進你的資料庫，以備未來撰寫文案時提供真實語料參考。
        """)

    st.markdown("---")

    st.markdown("## 2. 🧠 尋找素材：三大搜尋模式深度解析 (頁面 2)")
    st.markdown("當影片採收進系統後，你必須記得點擊左側邊欄的 **「🔄 重建向量資料庫」**，系統才會把新影片切成一塊塊的碎片存進大腦（ChromaDB）。")

    with st.expander("🔍 模式一：AI 語意搜尋 (找相似概念)", expanded=True):
        st.markdown("""
        - **原理**：這不是傳統的比對文字。系統會把你輸入的句子轉換成「數學座標（向量）」，然後去資料庫裡找離這個座標最近的對話。
        - **什麼時候用**：當你只記得一個模糊的概念，但不確定蕭博士原話怎麼講的時候。
        - **範例**：搜尋 `小孩上課很容易分心` ➔ 系統可能會找到博士講 `他眼睛到處看，坐不住` 的片段，即使完全沒有命中關鍵字。
        """)

    with st.expander("🔍 模式二：精確關鍵字搜尋 (必須包含該字)", expanded=True):
        st.markdown("""
        - **原理**：經典的文本比對（類似網頁的 Ctrl+F），利用向量資料庫的 `$contains` 底層語法，強制作出精準打擊。
        - **什麼時候用**：當你非常肯定影片中有出現專有名詞，且不能容許 AI 找錯的時候。
        - **特點**：系統會以**黃色螢光筆**將你的關鍵字標示出來，方便你快速掃視，且若只鎖定一支影片搜尋，下方還會展開整支影片的完整逐字稿讓你「地毯式檢查」。
        """)

    with st.expander("🔍 模式三：✨ 魔法搜尋 (擷取學員見證的神器)", expanded=True):
        st.markdown("""
        - **原理 (HyDE 架構)**：這是在語意搜尋上疊加的一層魔法。當你搜尋「早點報名」這種短詞時，如果直接搜，會搜到一堆在講時間的廢話。
          **魔法搜尋會先「偷偷」呼叫 GPT-4o，告訴它你是一個廣告製片，要它把「早點報名」擴寫成一段真實的學員見證對話（例如：「我真是相見恨晚，早點幫小孩報名就好了」），然後系統再拿這段充滿情緒的長句子去資料庫做比對！**
        - **什麼時候用**：當你要「挖礦」找廣告素材、找痛點共鳴、找學員痛哭流涕的感言時。
        - **範例**：你輸入 `背單字很痛苦` ➔ AI 擴寫成 `我以前每天逼小孩背十個單字，搞得親子關係破裂，超級痛苦...` ➔ 資料庫根據這個擴寫句子，完美找到之前某個媽媽的真實慘痛案例。
        """)

    st.markdown("---")

    st.markdown("## 3. ✍️ 內容精煉與文案生成 (頁面 3、頁面 4、頁面 5)")
    st.markdown("當你有了逐字稿和素材，系統能將這些生硬的文字變成高轉換率的行銷素材。這裡的邏輯高度依賴「Prompt（提示詞指令）」的串接。")

    with st.expander("⚙️ Prompt 核心大腦 (頁面 5 - Prompt 管理)", expanded=True):
        st.markdown("""
        - **串接邏輯**：這是系統的「大腦規則庫」。你在這裡寫的所有指令（例如：如何分析痛點、如何用蕭博士語氣），都會被儲存在系統底層（`core/prompts.json`）。
        - **預設 Prompt 的威力**：請務必在此頁面將你最常用、寫得最好的一組 Prompt 設為「預設」。這個預設指令將會自動綁定到：
          1. **YouTube 自動採收**：下載完影片後自動生成的文章，就是用這個 Prompt。
          2. **文案精煉頁面**：當你進到文案精煉頁，它框裡的指令也是預設抓這個。
        """)

    with st.expander("✨ 互動式文案精煉 (頁面 3)", expanded=False):
        st.markdown("""
        - 如果你在採收影片時沒有勾選「自動生成文案」，或是你覺得剛才自動生成的寫得不夠好，你可以來到這個頁面。
        - **做法**：選擇你想重寫的影片逐字稿，切換你想實驗的 Prompt（或選最新最高階的 **GPT-5.4** 模型），讓 AI 重新咀嚼逐字稿，輸出成一篇乾淨漂亮的「SoR 策略文案」。
        """)
        
    with st.expander("🚀 多平台行銷素材佈署 (頁面 4)", expanded=False):
        st.markdown("""
        - **串接邏輯**：當「SoR 策略文案」誕生後，這個頁面負責負責把它「變化」成適合各個主流社群平台的尺寸。
        - **發布流程**：
          1. 選擇一篇你想發布的策略文案。
          2. 按下一鍵生成，GPT-4o 會同時幫你寫出：**短巧的 Threads 貼文、圖文並茂的 FB 貼文、LINE OA 的互動式選單廣播文（甚至附上 JSON 格式提供工程師直接用）**。
        """)

with tab_dev:
    st.markdown("""
    ## 🏗️ 系統架構與底層開發指南
    本系統使用 **Python 3.10+** 開發，採用 **Streamlit** 作為前端框架，並與大量的 AI SDK 與影音處理函式庫深度結合。

    ---

    ### 1. 📂 核心目錄結構
    ```text
    youtubedb/
    ├── Home.py                  # 系統入口點 (執行: streamlit run Home.py)
    ├── requirements.txt         # 系統依賴套件清單
    ├── data/                    # (執行期間自動生成) 存放所有 .mp4, .srt, .txt 與 chroma 索引
    ├── core/                    # 系統核心邏輯層
    │   ├── config.py            # 全域變數、路徑設定、預設參數
    │   ├── utils.py             # 核心大腦。包含 OpenAI/Gemini 連線、ChromaDB 管理、Whisper 轉錄函式
    │   ├── .env                 # API Keys 放置處
    │   └── prompts.json         # 給定 LLM 的系統級提示詞 (由頁面 5 動態修改)
    └── pages/                   # Streamlit 前端路由頁面
        ├── 1_🎬_YouTube採收.py
        ├── 2_📚_知識庫搜尋.py
        └── ...
    ```

    ---

    ### 2. 🗄️ 向量資料庫 (ChromaDB) 實作細節
    系統的所有檢索依賴於本地端的 `chromadb`。實作細節位於 `core/utils.py` 中的 `update_vector_db()`。
    - **Chunking (切塊邏輯)**：我們並沒有直接將數萬字的逐字稿直接 Embedded。系統將 `.srt` 檔案解析後，**每 5 行字幕合併為一個 Document** 進行向量化，這樣可以確保搜尋出來的結果有足夠的上下文跨度（約 30-40 秒的語境）。
    - **Embedding Model**：預設使用 `sentence-transformers/all-MiniLM-L6-v2` (或依賴於 ChromaDB 內部預設)。其在速度與中文/英文混合的語意捕捉上達到平衡。
    - **Metadata**：寫入時，除了文本 `document` 外，還打上了 `source` (影片檔名)、`start_time`、`end_time` 的 Metadata。這使得頁面 2 中可以快速製作「影片來源篩選器 (Filter)」。

    ---

    ### 3. ✨ 魔法搜尋 (HyDE) 實作邏輯 (Hybrid Document Embeddings)
    位於 `pages/2_📚_知識庫搜尋.py` 的魔法搜尋，是 RAG (Retrieval-Augmented Generation) 架構的高階變體。
    - **傳統問題**：RAG 由於是數學距離比對，當 User 輸入異常簡短的字詞 ("早點報名") 時，其 Embedding Vector 會嚴重偏斜，導致對應不到真實世界冗長口語對話的 Vector。
    - **HyDE 解法**：我們在 Query 進入 ChromaDB **之前**，攔截了該字詞，並拋給 GPT-4o 進行一次 Zero-shot 的文本生成（模擬學員見證）。生成的回應（約 50 字長）取代了原始短句輸入到 Embedding 函數中，藉由大量生成的近似語境詞彙（如「後悔」、「浪費錢」、「終於懂了」），極大幅度增加了與底層真實逐字稿 Vector 的 Cosine Similarity 命中率。

    ---

    ### 4. 🤖 模型調用規範
    在各頁面擴展新功能時，請一律使用 `core/utils.py` 裡的 Client 來作呼叫：
    - `openai_client`：用於高強度寫作、HyDE 擴充、Whisper 轉錄。
    - `genai_client`：備用方案，用於處理 Gemini-Flash 批次生成或長上下文摘要。
    - **Streaming (串流輸出)**：請優先使用 `utils.generate_sor_stream()`。它回傳的是 Python Generator，前端可直接搭配 `st.write_stream()` 呈現打字機效果，大幅避免使用者枯等。

    ---

    ### 5. 🌐 伺服器部署注意事項
    - **Port 衝突**：Streamlit 預設走 `8501`。若本機/雲端有其他系統，請以 `streamlit run Home.py --server.port 8502` 閃避。
    - **FFmpeg 依賴**：伺服器上**絕對不可缺少** `ffmpeg` 套件，否則 Whisper 的 `pydub` 資料串流會直接 crash。
    - **長時間運行**：強烈建議使用 `PM2` 或 `systemd` 包裝 Streamlit 啟動指令，嚴禁直接在 SSH 中用 foreground 執行，以免連線中斷導致爬蟲或轉錄中途死亡。
    """)
