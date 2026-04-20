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
    top_k = st.slider("顯示搜尋結果數量", 1, 10, 3)
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

# ── 搜尋輸入框 ────────────────────────────────────────────────────────────────
query = st.text_input(
    "🔍 搜尋全站影片知識庫",
    value=st.session_state.quick_query,
    placeholder="輸入問題或關鍵詞，AI 會跨影片搜尋最相關的片段...",
)

# ── 搜尋結果 ──────────────────────────────────────────────────────────────────
if query:
    try:
        from utils import get_chroma_collection
        collection = get_chroma_collection()
        results = collection.query(query_texts=[query], n_results=top_k)

        if results["documents"] and results["documents"][0]:
            st.markdown(f"**🎯 找到 {len(results['documents'][0])} 個相關片段**")
            st.markdown("---")

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
                        st.info(doc)

                        # --- ✂️ 一鍵剪輯區域 ---
                        if vid and vid != "local_text":
                            if st.button(f"✂️ 剪輯此片段 (#{i+1})", key=f"cut_{i}"):
                                with st.spinner("正在精準切割中..."):
                                    try:
                                        from tool_smart_cutter import SmartCutterEngine
                                        from config import DATA_DIR
                                        from pathlib import Path
                                        
                                        engine = SmartCutterEngine()
                                        
                                        # 推測資料夾路徑 (檔名通常是 id_標題.srt，標題可能需要 sanitize)
                                        # 其實最佳方式是直接用影片標題，但在這裡可以用 source_file 去找
                                        title_part = source_file.replace(f"{vid}_", "").replace(".srt", "")
                                        # 去掉非法字元 (對齊 Harvester 的邏輯)
                                        safe_title = re.sub(r'[\\/*?:"<>|]', "", title_part).strip()
                                        video_folder = DATA_DIR / "outputs" / safe_title
                                        
                                        if not video_folder.exists():
                                            # 備案：模糊搜尋資料夾
                                            candidates = list((DATA_DIR / "outputs").glob(f"*{vid}*"))
                                            if candidates: video_folder = candidates[0]

                                        res = engine.cut(
                                            video_folder=video_folder,
                                            start_time=start_s,
                                            end_time=end_s,
                                            output_name=f"[精華]_{query[:10]}_{int(start_s)}s"
                                        )
                                        
                                        if res["status"] == "success":
                                            st.success(f"✅ 剪輯完成！檔案已存於：`{res['file']}`")
                                            st.balloons()
                                        else:
                                            st.error(f"❌ 剪輯失敗：{res['message']}")
                                    except Exception as e:
                                        st.error(f"❌ 系統錯誤：{e}")

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
