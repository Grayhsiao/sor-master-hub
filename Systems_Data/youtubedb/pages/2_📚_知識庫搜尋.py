import streamlit as st
import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="知識庫搜尋 · 蕭博士 SoR", page_icon="📚", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0a1f3d 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(99,102,241,0.25);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }
.result-card {
    background: rgba(22,27,34,0.95); border: 1px solid rgba(48,54,61,0.8);
    border-radius: 14px; padding: 1.5rem; margin-bottom: 1.2rem;
    transition: border-color 0.2s;
}
.result-card:hover { border-color: rgba(99,102,241,0.5); }
.result-rank {
    display: inline-block; background: rgba(99,102,241,0.15); color: #818cf8;
    border-radius: 20px; padding: 0.15rem 0.75rem; font-size: 0.78rem; font-weight: 600; margin-bottom: 0.6rem;
}
.quick-btn-wrap { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)

# ── 側邊欄 ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    top_k = st.slider("顯示搜尋結果數量", 1, 50, 10)
    st.markdown("---")
    if st.button("🔄 重建向量資料庫", use_container_width=True):
        with st.spinner("掃描並建立索引中..."):
            try:
                from config import SOURCE_DIR, INDEX_FILE, DB_PATH
                from utils import get_chroma_collection, parse_srt_file, chunk_text_generic
                import json, chromadb

                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    video_map = json.load(f)

                srt_files = glob.glob(os.path.join(SOURCE_DIR, "*.srt"))
                txt_files = [f for f in glob.glob(os.path.join(SOURCE_DIR, "*.txt"))
                             if not f.endswith("_strategy.txt")]

                docs, metas, ids = [], [], []
                for file_path in srt_files:
                    fn = os.path.basename(file_path)
                    if fn not in video_map:
                        continue
                    vid = video_map[fn]
                    chunks = parse_srt_file(file_path)
                    for i, c in enumerate(chunks):
                        docs.append(c["text"])
                        metas.append({"source": fn, "video_id": vid,
                                      "start_time": c["start"], "end_time": c["end"]})
                        ids.append(f"{fn}_{i}")

                for file_path in txt_files:
                    fn = os.path.basename(file_path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    chunks = chunk_text_generic(content)
                    for i, chunk in enumerate(chunks):
                        docs.append(chunk)
                        metas.append({"source": fn, "video_id": "local_text",
                                      "start_time": 0, "end_time": 0})
                        ids.append(f"{fn}_{i}")

                if docs:
                    coll = get_chroma_collection()
                    client = chromadb.PersistentClient(path=str(DB_PATH))
                    try: client.delete_collection(name=coll.name)
                    except: pass
                    coll = get_chroma_collection()
                    coll.add(documents=docs, metadatas=metas, ids=ids)
                    st.success(f"✅ 已重建：{len(docs)} 個知識點")
                else:
                    st.warning("⚠️ 找不到任何來源檔案")
            except Exception as e:
                st.error(f"❌ 重建失敗：{e}")

# ── 標題 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>📚 知識庫搜尋</h1>
    <p>跨影片 AI 語意搜尋，直接跳到影片對應時間點播放，快速找到關鍵 SoR 知識</p>
</div>
""", unsafe_allow_html=True)

# ── 快速查詢按鈕 ──────────────────────────────────────────────────────────────
st.markdown("**💡 快速查詢**")
quick_queries = {
    "🔰 什麼是 SOR？": "什麼是 SOR Science of Reading",
    "👂 什麼是 PA？": "什麼是 PA 音素覺察",
    "💣 三大地雷": "台灣人學英文的三大地雷",
    "🧠 腦科學原理": "大腦如何學會閱讀 腦科學",
    "🗣️ 語音覺察": "語音覺察 phonological awareness",
}

if "quick_query" not in st.session_state:
    st.session_state.quick_query = ""

cols = st.columns(len(quick_queries))
for col, (label, q) in zip(cols, quick_queries.items()):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.quick_query = q

# ── 進階篩選 ────────────────────────────────────────────────────────────────
st.markdown("**🔍 進階選項：指定影片搜尋**")
try:
    from config import INDEX_FILE
    import json
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        video_map = json.load(f)
    # 萃取出檔名清單供使用者選擇
    all_video_files = list(video_map.keys())
    selected_videos = st.multiselect(
        "選擇要搜尋的影片 (留空代表搜尋全部)",
        options=all_video_files,
        format_func=lambda x: x.replace(".srt", "")  # 隱藏副檔名讓介面更乾淨
    )
except Exception:
    selected_videos = []
    st.warning("無法讀取影片清單，將搜尋全站。")

st.divider()
query = st.text_input(
    "🔍 搜尋全站影片知識庫",
    value=st.session_state.quick_query,
    placeholder="輸入問題或關鍵詞，AI 會跨影片搜尋最相關的片段...",
)

search_mode = st.radio(
    "搜尋模式", 
    ["🧠 AI 語意搜尋 (找相似概念)", "📝 精確關鍵字搜尋 (必須包含該字)", "✨ 魔法搜尋 (AI 擴充找學員見證)"], 
    horizontal=True,
    help="語意搜尋可找到意思相近的內容；魔法搜尋則會讓 AI 模擬學員口吻，用更長的情境幫你把相關見證挖出來！"
)

# ── 搜尋結果 ──────────────────────────────────────────────────────────────────
if query:
    try:
        from utils import get_chroma_collection
        collection = get_chroma_collection()
        
        # 建立過濾條件
        where_clause = None
        if selected_videos:
            if len(selected_videos) == 1:
                where_clause = {"source": selected_videos[0]}
            else:
                where_clause = {"source": {"$in": selected_videos}}
                
        # 執行查詢
        is_exact = "精確" in search_mode
        is_magic = "魔法" in search_mode
        
        # 決定最終要送去搜尋的字詞
        search_query = query
        
        if is_magic:
            with st.spinner("✨ AI 正在模擬學員情境，擴充搜尋詞彙..."):
                from dotenv import load_dotenv
                import os
                import openai
                
                env_path = os.path.join(os.path.dirname(__file__), "..", "core", ".env")
                load_dotenv(env_path, override=True)
                
                o_key = os.getenv("OPENAI_API_KEY")
                if o_key:
                    client = openai.OpenAI(api_key=o_key)
                    try:
                        prompt = f"""使用者想在「蕭博士 SoR 美語」的課程影片中，擷取特定的「學員見證」來剪輯廣告。
請結合使用者輸入的關鍵字：「{query}」，擴寫成一段大約 40~50 字的「真實學員口吻」的逐字稿片段。
例如：如果關鍵字是「相見恨晚」，你可以寫「我以前花了好多錢都學不會，如果能早點認識蕭博士，早點接觸這套教材就好了，真的是相見恨晚...」。
請注意：不要有任何開頭解析，不要加引號，不要做過多無謂的鋪陳，直接給出一段口語化、充滿情感的模擬見證原話即可。"""
                        
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "你是一個專業的廣告製片，擅長抓出受眾會產生共鳴的真情流露話語。"},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=150
                        )
                        search_query = response.choices[0].message.content.strip()
                        st.info(f"**✨ 魔法搜尋已啟用！AI 幫你擴寫成真正的學員語氣：**\n\n> {search_query}")
                    except Exception as e:
                        st.error(f"AI 擴寫失敗，將使用原始關鍵字。錯誤：{e}")
                else:
                    st.warning("未設定 OpenAI API Key，無法使用魔法搜尋，將退回一般語意搜尋。")

        if is_exact:
            # 精確搜尋 (Keyword Matach)
            # 使用 get 與 $contains
            kwargs = {"where_document": {"$contains": query}}
            if where_clause:
                kwargs["where"] = where_clause
            raw_results = collection.get(**kwargs)
            
            # 將 get 的結果格式轉換得跟 query 一樣，並配合 top_k
            docs = raw_results["documents"][:top_k] if raw_results["documents"] else []
            metas = raw_results["metadatas"][:top_k] if raw_results["metadatas"] else []
            results = {"documents": [docs] if docs else [], "metadatas": [metas] if metas else []}
        else:
            # 語意搜尋 (Semantic Search) & 魔法搜尋
            if where_clause:
                results = collection.query(query_texts=[search_query], n_results=top_k, where=where_clause)
            else:
                results = collection.query(query_texts=[search_query], n_results=top_k)

        if results.get("documents") and results["documents"] and results["documents"][0]:
            st.markdown(f"**🎯 找到 {len(results['documents'][0])} 個相關片段**")
            st.markdown("---")
            
            # 如果只選了一支影片，無論何種搜尋模式，都在結果上方提供全文預覽
            if selected_videos and len(selected_videos) == 1:
                source_file = selected_videos[0]
                from config import SOURCE_DIR
                srt_path = os.path.join(SOURCE_DIR, source_file)
                if os.path.exists(srt_path):
                    with st.expander(f"📖 預覽【{source_file.replace('.srt', '')}】完整逐字稿", expanded=False):
                        from utils import clean_srt_to_text
                        with open(srt_path, 'r', encoding='utf-8') as f:
                            raw_srt = f.read()
                            clean_text = clean_srt_to_text(raw_srt)
                            st.text_area("完整逐字稿 (純文字)", value=clean_text, height=300, disabled=True)
            
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                start_s = int(meta.get("start_time", 0))
                end_s = int(meta.get("end_time", 0))
                vid = meta.get("video_id", "")
                source_file = meta.get("source", "")

                with st.container():
                    st.markdown(f'<div class="result-rank">#{i+1} 結果</div>', unsafe_allow_html=True)

                    cl, cr = st.columns([1.4, 2])
                    with cl:
                        st.markdown(f"**📁 來源：`{source_file}`**")
                        if vid and vid != "local_text":
                            embed_url = f"https://www.youtube.com/embed/{vid}?start={start_s}&end={end_s}&rel=0"
                            st.markdown(
                                f'<iframe width="100%" height="225" src="{embed_url}" '
                                f'frameborder="0" allowfullscreen style="border-radius:10px;"></iframe>',
                                unsafe_allow_html=True
                            )
                            st.caption(f"⏱ {start_s}s ~ {end_s}s &nbsp;|&nbsp; [在 YouTube 開啟 ↗](https://youtu.be/{vid}?t={start_s}s)")
                        else:
                            st.info("📄 本地文件來源，無對應影片")

                    with cr:
                        st.markdown("**📝 片段內容**")
                        
                        # 實作關鍵字 Highlight
                        import re
                        # 為了不破壞原本的 doc，我們用正則表達式把 query 包裝成帶有顏色的 HTML
                        if query:
                            # 轉義處理避免正則表達式錯誤
                            escaped_query = re.escape(query)
                            # 使用 HTML mark 標籤上色 (Streamlit info 支援有限，我們改用 markdown)
                            highlighted_doc = re.sub(
                                f"({escaped_query})", 
                                r'<mark style="background-color: #ffe066; color: black; font-weight: bold; border-radius: 3px; padding: 0 2px;">\1</mark>', 
                                doc, 
                                flags=re.IGNORECASE
                            )
                            # 使用自訂的 UI 框取代 st.info，以支援 HTML 渲染
                            st.markdown(f"""
                            <div style="background-color: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6; color: #E6EDF3; font-size: 0.95rem; line-height: 1.5;">
                                {highlighted_doc}
                            </div>
                            <br>
                            """, unsafe_allow_html=True)
                        else:
                            st.info(doc)

                        strategy_path = os.path.join(
                            os.path.dirname(meta.get("source", "")),
                            source_file.replace(".srt", "_strategy.txt")
                        )
                        # 嘗試直接路徑
                        from config import SOURCE_DIR
                        strategy_full = os.path.join(SOURCE_DIR, source_file.replace(".srt", "_strategy.txt"))
                        if os.path.exists(strategy_full):
                            with st.expander("✨ 查看 SoR 策略文案"):
                                with open(strategy_full, "r", encoding="utf-8") as sf:
                                    st.markdown(sf.read())
                        else:
                            st.caption("ℹ️ 此影片尚無策略文案，可至「文案精煉」頁生成")

                    st.divider()
        else:
            st.warning("❌ 查無相關資料，請嘗試不同關鍵字或先「重建向量資料庫」")

    except Exception as e:
        st.error(f"❌ 查詢失敗：{e}")
        st.info("💡 如果是初次使用，請先點擊左側「🔄 重建向量資料庫」")
