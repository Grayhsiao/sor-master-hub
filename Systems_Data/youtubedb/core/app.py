import streamlit as st
import os
import glob
import json
from config import SOURCE_DIR, INDEX_FILE, DB_PATH
from utils import get_embedding_function, parse_srt_file, get_chroma_collection

# === 1. 資料處理邏輯 ===
def process_all_files():
    if not os.path.exists(INDEX_FILE):
        return None, f"❌ 找不到 {INDEX_FILE}，請建立對照表。"
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        video_map = json.load(f)

    srt_files = glob.glob(os.path.join(SOURCE_DIR, "*.srt"))
    txt_files = [f for f in glob.glob(os.path.join(SOURCE_DIR, "*.txt")) if not f.endswith("_strategy.txt")]
    
    if not srt_files and not txt_files:
        return None, f"❌ 在 {SOURCE_DIR} 資料夾內找不到任何資料來源 (.srt 或 .txt)。"

    docs, metas, ids = [], [], []
    processed_count = 0

    st.write("正在掃描檔案...")
    for file_path in srt_files:
        file_name = os.path.basename(file_path)
        if file_name not in video_map:
            st.warning(f"⚠️ 跳過 {file_name}：在 json 表中找不到對應的 ID")
            continue
            
        video_id = video_map[file_name]
        processed_count += 1

    # 處理純文字檔
    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        st.write(f"📄 正在處理文字：{file_name}")
        
        from utils import chunk_text_generic
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = chunk_text_generic(content)
        for i, chunk in enumerate(chunks):
            docs.append(chunk)
            metas.append({
                "source": file_name, 
                "video_id": "local_text", # 用於區分非影片來源
                "start_time": 0, 
                "end_time": 0
            })
            ids.append(f"{file_name}_{i}")
        processed_count += 1

    if processed_count == 0:
        return None, "❌ 沒有任何檔案被成功處理。"

    collection = get_chroma_collection()
    # Recreate collection to cleanup old data
    import chromadb
    client = chromadb.PersistentClient(path=str(DB_PATH))
    try: client.delete_collection(name=collection.name)
    except: pass
    collection = get_chroma_collection()
    
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return collection, f"✅ 成功匯入 {processed_count} 個影片，共 {len(docs)} 個知識點！"

# === 2. 網頁介面 ===
st.set_page_config(page_title="蕭博士 AI 知識庫 (SoR Optimized)", layout="wide")
st.title("📚 蕭博士 Science of Reading 知識庫系統")

# 側邊欄設計
with st.sidebar:
    st.header("⚙️ 系統管理")
    st.info("請將字幕檔 (.srt) 放入 sources 資料夾。系統會自動抓取對應的策略文案 (_strategy.txt)。")
    
    if st.button("🔄 重建資料庫"):
        with st.spinner("正在掃描並處理檔案..."):
            col, msg = process_all_files()
            if col: st.success(msg)
            else: st.error(msg)
            
    st.divider()
    top_k = st.slider("顯示搜尋結果量", 1, 10, 3)
    st.caption("AI 會根據關聯度回報最相關的片段。")

# 快速引導區
st.subheader("💡 快速導覽")
queries = {
    "🔰 什麼是 SOR？": "什麼是 SOR Science of Reading",
    "👂 什麼是 PA？": "什麼是 PA 音素覺察",
    "💣 三大地雷": "台灣人學英文的三大地雷",
    "🧠 腦科學原理": "大腦如何學會閱讀 腦科學"
}
cols = st.columns(len(queries))
query = None
for i, (label, q_text) in enumerate(queries.items()):
    if cols[i].button(label):
        query = q_text

if not query:
    query = st.text_input("🔍 搜尋全站影片...", placeholder="輸入關鍵字，AI 會跨影片搜尋...")

# 顯示搜尋結果
if query:
    try:
        collection = get_chroma_collection()
        results = collection.query(query_texts=[query], n_results=top_k)
        
        st.divider()
        if results['documents'] and len(results['documents'][0]) > 0:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                start_s, end_s = int(meta['start_time']), int(meta['end_time'])
                vid = meta['video_id']
                source_file = meta['source']
                
                with st.container():
                    col1, col2 = st.columns([1.5, 2])
                    with col1:
                        st.markdown(f"**📺 來源：`{source_file}`**")
                        
                        # 嵌入播放器 (僅限影片)
                        if vid != "local_text":
                            embed_url = f"https://www.youtube.com/embed/{vid}?start={start_s}&end={end_s}&rel=0"
                            iframe_code = f"""<iframe width="100%" height="280" src="{embed_url}" frameborder="0" allowfullscreen></iframe>"""
                            st.markdown(iframe_code, unsafe_allow_html=True)
                            st.caption(f"⏱ 片段範圍: {start_s}s ~ {end_s}s | [在 YouTube 開啟](https://youtu.be/{vid}?t={start_s}s)")
                        else:
                            st.warning("📄 此來源為本地文件，無對應影片。")

                    with col2:
                        st.subheader("📝 片段內容")
                        st.info(doc)
                        
                        # 檢查並顯示 SoR 策略文案
                        strategy_path = os.path.join(SOURCE_DIR, source_file.replace(".srt", "_strategy.txt"))
                        if os.path.exists(strategy_path):
                            with st.expander("✨ 展開查看此影片的【SoR 深度策略文案】"):
                                with open(strategy_path, 'r', encoding='utf-8') as sf:
                                    st.markdown(sf.read())
                            
                            # 新增：整合行銷引擎按鈕
                            if st.button(f"🚀 產出此影片的全平台行銷素材", key=f"marketing_{vid}"):
                                try:
                                    from export_marketing_assets import MarketingEngine
                                    engine = MarketingEngine()
                                    # 注意：這裡我們需要一個能針對特定影片導出的方法
                                    # 為了簡單，我們先導出全部，或稍後優化 MarketingEngine
                                    engine.export_all() 
                                    st.success(f"✅ 素材已導出至 `data/marketing_assets/` 資料夾！")
                                    st.info(f"包含：Line 文字、Threads 短文、Line Flex Message (JSON)")
                                except Exception as me_err:
                                    st.error(f"行銷引擎執行失敗：{me_err}")
                        else:
                            st.caption("ℹ️ 此影片尚無策略文案，可執行 `refine_strategy_ai.py` 生成。")
                    st.divider()
        else:
            st.warning("查無相關資料。")
    except Exception as e:
        st.error(f"查詢出錯：{e} (請嘗試重建資料庫)")