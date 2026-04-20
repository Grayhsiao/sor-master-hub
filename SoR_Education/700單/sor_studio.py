import streamlit as st
import pandas as pd
import numpy as np
import os, sys, ast, json, io, time, base64
from PIL import Image
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

# ─── 設定 ───────────────────────────────────────────────────
SCRIPT_XLSX   = "700單腳本.xlsx"
LIST_XLSX     = "700單_量產清單.xlsx"
OFFICIAL_CSV  = "700單_官方對照表.csv"
DICTIONARY_XLSX = "字典底層資料 的副本.xlsx"
AUDIO_DIR     = "音檔"
OUTPUT_DIR    = "output_videos"
RECORDINGS_DIR = "recordings"  # 每個單字的分段錄音暫存
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

st.set_page_config(
    page_title="🎬 SoR Studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* 側邊欄 */
  [data-testid="stSidebar"] { background: #0f0f1a; }
  [data-testid="stSidebar"] * { color: #e0e0f0 !important; }

  /* 卡片 */
  .card {
    background: #1a1a2e;
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .card-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #7c7caa;
    margin-bottom: 10px;
  }

  /* 單字大標題 */
  .word-hero {
    font-size: 52px;
    font-weight: 700;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
  }
  .word-subtitle { font-size: 14px; color: #888; margin-top: 4px; }

  /* 分鏡區塊 */
  .scene-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 12px;
    background: #111128;
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 3px solid #4444aa;
  }
  .scene-idx {
    font-size: 11px;
    font-weight: 700;
    color: #7c7caa;
    min-width: 60px;
    padding-top: 2px;
  }
  .scene-label { font-size: 15px; color: #c0c0e0; }

  /* 狀態標籤 */
  .badge-ok   { background:#16a34a22; color:#4ade80; border:1px solid #16a34a; border-radius:20px; padding:2px 10px; font-size:12px; }
  .badge-warn { background:#ca8a0422; color:#fbbf24; border:1px solid #ca8a04; border-radius:20px; padding:2px 10px; font-size:12px; }
  .badge-miss { background:#dc262622; color:#f87171; border:1px solid #dc2626; border-radius:20px; padding:2px 10px; font-size:12px; }

  /* 錄音棚大按鈕 */
  .big-next-btn {
    font-size: 28px;
    font-weight: 700;
    padding: 20px 40px;
    border-radius: 16px;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    border: none;
    cursor: pointer;
    width: 100%;
    letter-spacing: 0.05em;
    transition: transform 0.1s;
  }
  .big-next-btn:active { transform: scale(0.96); }

  /* 時間軸記錄列表 */
  .timeline-item {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 8px 12px;
    border-radius: 8px;
    background: #0d1117;
    margin-bottom: 6px;
    font-size: 14px;
  }
  .timeline-ts  { color: #60a5fa; font-family: monospace; min-width: 65px; }
  .timeline-lbl { color: #e0e0f0; }
  .timeline-del { color: #f87171; cursor: pointer; margin-left: auto; }

  /* 腳本顯示框 */
  .script-box {
    background: #0f1117;
    border: 1px solid #2d2d4e;
    border-radius: 8px;
    padding: 18px 22px;
    font-size: 15px;
    line-height: 1.85;
    color: #d0d0f0;
    white-space: pre-wrap;
    max-height: 420px;
    overflow-y: auto;
  }

  /* 分隔線 */
  hr.dim { border-color: #2d2d4e; }
</style>
""", unsafe_allow_html=True)

# ─── 資料載入 ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    # ── 量產清單
    df_list = pd.read_excel(LIST_XLSX)
    df_list.columns = df_list.columns.str.strip()

    # ── 官方章節對照
    if os.path.exists(OFFICIAL_CSV):
        df_official = pd.read_csv(OFFICIAL_CSV)
        df_official = df_official[['word', '700Chapter', '700ChapterName']].drop_duplicates('word')
        df_list = pd.merge(df_list, df_official, on='word', how='left')

    # ── 字典底層 (抓取語調 Intonation)
    if os.path.exists(DICTIONARY_XLSX):
        df_dict = pd.read_excel(DICTIONARY_XLSX)
        df_dict = df_dict[['word', 'Intonation']].dropna(subset=['word']).drop_duplicates('word')
        df_list = pd.merge(df_list, df_dict, on='word', how='left')

    # ── 腳本
    df_script = pd.read_excel(SCRIPT_XLSX, header=None)
    df_script.columns = ['order','word','cultural_ref','example_sentences',
                          'phrases','script','status','extra']
    df_script['word_lower'] = df_script['word'].astype(str).str.strip().str.lower()
    return df_list, df_script

def get_script_for_word(df_script, word_str):
    match = df_script[df_script['word_lower'] == word_str.strip().lower()]
    if not match.empty:
        return match.iloc[0]
    return None

def get_audio_path(word):
    safe = word.strip().lower()
    for ext in ['.m4a', '.mp3', '.wav']:
        p = os.path.join(AUDIO_DIR, safe + ext)
        if os.path.exists(p): return p
    return None

def get_recording_dir(word):
    d = os.path.join(RECORDINGS_DIR, word.strip().lower())
    os.makedirs(d, exist_ok=True)
    return d

def get_markers_path(word):
    return os.path.join(get_recording_dir(word), "markers.json")

def load_markers(word):
    p = get_markers_path(word)
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return []

def save_markers(word, markers):
    with open(get_markers_path(word), 'w') as f:
        json.dump(markers, f, ensure_ascii=False, indent=2)

# ─── 音標預覽 ─────────────────────────────────────────────────
def render_matrix_preview(minum_str, intonation_str):
    try:
        from matrix_stitcher import stitch_matrix_phonetics
        img = stitch_matrix_phonetics(minum_str, intonation_str, max_w=700, target_h=120)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception as e:
        return None

# ─── 生成場景序列 ─────────────────────────────────────────────
def get_scene_labels(intonation_str, has_sent1, has_sent2, has_img1, has_img2):
    scenes = [
        ("S1", "🔤 單字介紹"),
        ("S2", "📐 音標全覽"),
    ]
    into_list = list(intonation_str.replace(" ","")) if intonation_str else []
    for i, tone in enumerate(into_list):
        scenes.append((f"R{i}", f"🎵 第 {i+1} 排音節 ({tone})"))
    if has_sent1: scenes.append(("Sent1", "💬 例句一"))
    if has_img1:  scenes.append(("Img1",  "🖼️ 圖片一"))
    if has_sent2: scenes.append(("Sent2", "💬 例句二"))
    if has_img2:  scenes.append(("Img2",  "🖼️ 圖片二"))
    return scenes

# ─── 主介面 ──────────────────────────────────────────────────
df_list, df_script = load_data()

# ══════════════════ 側邊欄 ══════════════════
with st.sidebar:
    st.markdown("### 🎬 SoR Studio")
    st.markdown("---")

    # 章節篩選
    all_chaps = sorted(df_list['700ChapterName'].dropna().unique().tolist())
    sel_chap = st.selectbox("📁 選擇章節", ["全部單字"] + all_chaps)

    search = st.text_input("🔍 搜尋單字", placeholder="輸入單字...")
    
    # 過濾邏輯
    df_filtered = df_list.copy()
    if sel_chap != "全部單字":
        df_filtered = df_filtered[df_filtered['700ChapterName'] == sel_chap]
    if search:
        df_filtered = df_filtered[df_filtered['word'].str.contains(search, case=False, na=False)]
    
    words_all = df_list['word'].dropna().astype(str).tolist()
    words_filtered = df_filtered['word'].dropna().astype(str).tolist()

    st.markdown(f"<small style='color:#666'>共 {len(words_filtered)} / {len(words_all)} 個單字</small>", unsafe_allow_html=True)

    # 計算狀態
    def word_status(w):
        has_audio = get_audio_path(w) is not None
        markers = load_markers(w)
        has_markers = len(markers) > 0
        if has_audio and has_markers: return "🟢"
        elif has_audio: return "🟡"
        else: return "🔴"

    selected_word = st.radio(
        "單字列表",
        words_filtered[:60],  # 顯示前60個避免過長
        format_func=lambda w: f"{word_status(w)} {w}",
        label_visibility="collapsed"
    )
    if len(words_filtered) > 60:
        st.caption(f"⚠️ 僅顯示前 60 筆，請用搜尋過濾")

# ══════════════════ 主區域 ══════════════════
if not selected_word:
    st.info("← 請從左側選擇一個單字開始")
    st.stop()

row_list   = df_list[df_list['word'] == selected_word].iloc[0] if selected_word in df_list['word'].values else None
row_script = get_script_for_word(df_script, selected_word)

# 取出欄位
minum_str    = str(row_list['minum'])       if row_list is not None else ""
intonation   = str(row_list['Intonation'])  if (row_list is not None and 'Intonation' in row_list and pd.notna(row_list['Intonation'])) else ""
chinese      = str(row_list['Chinese'])     if row_list is not None else ""
sentence1    = str(row_list.get('Sentence1',''))  if row_list is not None else ""
sentence2    = str(row_list.get('Sentence2',''))  if row_list is not None else ""
script_text  = str(row_script['script'])    if row_script is not None else ""
cultural_ref = str(row_script['cultural_ref']) if row_script is not None else ""
example_sents= str(row_script['example_sentences']) if row_script is not None else ""

has_sent1 = sentence1.strip() not in ['', 'nan']
has_sent2 = sentence2.strip() not in ['', 'nan']
has_img1  = False  # 暫不使用
has_img2  = False

# ─── 頂部：單字標題 ─────────────────────────────────────────
col_hero, col_status = st.columns([3, 1])
with col_hero:
    st.markdown(f'<div class="word-hero">{selected_word}</div>', unsafe_allow_html=True)
    chap_name = row_list['700ChapterName'] if '700ChapterName' in row_list else ""
    st.markdown(f'<div class="word-subtitle"><b>{chap_name}</b> ・ {chinese}</div>', unsafe_allow_html=True)

with col_status:
    audio_path = get_audio_path(selected_word)
    markers    = load_markers(selected_word)
    st.markdown("<br>", unsafe_allow_html=True)
    if audio_path and markers:
        st.markdown('<span class="badge-ok">✅ 音檔 + 分鏡就緒</span>', unsafe_allow_html=True)
    elif audio_path:
        st.markdown('<span class="badge-warn">🟡 有音檔，尚未標記</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-miss">🔴 尚未錄音</span>', unsafe_allow_html=True)

st.markdown("<hr class='dim'>", unsafe_allow_html=True)

# ─── 三欄佈局 ───────────────────────────────────────────────
col_script, col_studio, col_preview = st.columns([2.5, 2.5, 2])

# ════ 欄一：腳本 ════
with col_script:
    st.markdown('<div class="card-title">📝 腳本內容</div>', unsafe_allow_html=True)

    tab_script, tab_ref, tab_sent = st.tabs(["🎙️ 錄音腳本", "🎬 文化參考", "💬 例句/片語"])

    with tab_script:
        edited_script = st.text_area(
            "腳本（可直接修改）",
            value=script_text,
            height=350,
            key=f"script_{selected_word}",
            label_visibility="collapsed"
        )
        col_ai1, col_ai2 = st.columns([3, 1])
        with col_ai1:
            prompt = st.text_input("🤖 AI 改寫指令", placeholder="例：請把腳本改短，適合小學生，約200字", key=f"prompt_{selected_word}")
        with col_ai2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ 送出重寫", key=f"ai_btn_{selected_word}"):
                st.warning("⚙️ 此功能需要設定 Gemini API Key。請先在終端機設定 `GEMINI_API_KEY` 環境變數，或聯絡開發者協助設定。")

        if st.button("💾 儲存腳本至 Excel", key=f"save_script_{selected_word}", type="primary"):
            st.info("✏️ Excel 回寫功能開發中，目前請手動複製後貼回 Excel。")

    with tab_ref:
        st.markdown(f'<div class="script-box">{cultural_ref}</div>', unsafe_allow_html=True)

    with tab_sent:
        st.markdown(f'<div class="script-box">{example_sents}</div>', unsafe_allow_html=True)
        st.caption("片語關鍵字")
        st.code(str(row_script['phrases']) if row_script is not None else "")


# ════ 欄二：錄音棚 ════
with col_studio:
    st.markdown('<div class="card-title">🎬 單鍵分鏡錄製棚</div>', unsafe_allow_html=True)

    # 分鏡序列
    scene_labels = get_scene_labels(intonation, has_sent1, has_sent2, has_img1, has_img2)

    # 初始化 session state
    if f"rec_started_{selected_word}" not in st.session_state:
        st.session_state[f"rec_started_{selected_word}"] = False
    if f"rec_start_ts_{selected_word}" not in st.session_state:
        st.session_state[f"rec_start_ts_{selected_word}"] = None
    if f"rec_markers_{selected_word}" not in st.session_state:
        st.session_state[f"rec_markers_{selected_word}"] = list(markers)
    if f"rec_scene_idx_{selected_word}" not in st.session_state:
        st.session_state[f"rec_scene_idx_{selected_word}"] = 0

    is_recording = st.session_state[f"rec_started_{selected_word}"]
    scene_idx    = st.session_state[f"rec_scene_idx_{selected_word}"]
    cur_markers  = st.session_state[f"rec_markers_{selected_word}"]

    # 目前分鏡狀態 
    total_scenes = len(scene_labels)
    progress_pct = scene_idx / total_scenes if total_scenes else 0
    st.progress(progress_pct, text=f"進度：{scene_idx} / {total_scenes} 個分鏡")

    if scene_idx < total_scenes:
        sid, slabel = scene_labels[scene_idx]
        st.markdown(
            f'<div style="font-size:18px; padding:14px; border-radius:8px; background:#1a1a3e; margin-bottom:14px;">'
            f'目前分鏡 → <b style="color:#a78bfa">{slabel}</b></div>',
            unsafe_allow_html=True
        )
    else:
        st.success("🎉 所有分鏡錄製完成！請上傳音檔並合成影片。")

    # 大按鈕行為
    if not is_recording:
        if st.button("🎙️ 開始錄音", use_container_width=True, type="primary", key=f"start_rec_{selected_word}"):
            st.session_state[f"rec_started_{selected_word}"] = True
            st.session_state[f"rec_start_ts_{selected_word}"] = time.time()
            st.session_state[f"rec_markers_{selected_word}"] = []
            st.session_state[f"rec_scene_idx_{selected_word}"] = 0
            st.rerun()
    else:
        elapsed = time.time() - st.session_state[f"rec_start_ts_{selected_word}"]
        st.markdown(
            f'<div style="font-size:22px; color:#f87171; padding:10px; border-radius:8px; background:#1a0a0a; text-align:center;">'
            f'🔴 錄音中：<b>{elapsed:.1f}s</b></div>',
            unsafe_allow_html=True
        )

        btn_next_lbl = "🎬 下一鏡 (Next)" if scene_idx < total_scenes - 1 else "⏹️ 結束錄音"

        if st.button(btn_next_lbl, use_container_width=True, key=f"next_scene_{selected_word}"):
            ts_now = time.time() - st.session_state[f"rec_start_ts_{selected_word}"]
            cur_markers = st.session_state[f"rec_markers_{selected_word}"]
            if scene_idx < len(scene_labels):
                sid, slabel = scene_labels[scene_idx]
                cur_markers.append({"scene": sid, "label": slabel, "ts": round(ts_now, 3)})
            st.session_state[f"rec_markers_{selected_word}"] = cur_markers
            st.session_state[f"rec_scene_idx_{selected_word}"] = scene_idx + 1

            if scene_idx >= total_scenes - 1:
                st.session_state[f"rec_started_{selected_word}"] = False
                save_markers(selected_word, cur_markers)
                st.success("✅ 所有分鏡記錄完成並已儲存！請上傳音檔。")

            st.rerun()

        if st.button("❌ 取消錄音", key=f"cancel_rec_{selected_word}"):
            st.session_state[f"rec_started_{selected_word}"] = False
            st.rerun()

    st.markdown("---")

    # 時間軸顯示
    st.markdown('<div class="card-title">📍 分鏡時間軸</div>', unsafe_allow_html=True)
    display_markers = st.session_state.get(f"rec_markers_{selected_word}", cur_markers)
    if display_markers:
        for i, m in enumerate(display_markers):
            colA, colB, colC = st.columns([1.5, 3, 0.8])
            with colA: st.code(f"{m['ts']:.2f}s", language=None)
            with colB: st.write(m['label'])
            with colC:
                if st.button("🗑️", key=f"del_marker_{selected_word}_{i}"):
                    display_markers.pop(i)
                    st.session_state[f"rec_markers_{selected_word}"] = display_markers
                    save_markers(selected_word, display_markers)
                    st.rerun()
    else:
        st.caption("尚無分鏡記錄。開始錄音後按 Next 按鈕即可標記。")

    # 上傳音檔區域
    st.markdown("---")
    st.markdown('<div class="card-title">📂 上傳錄音檔</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("上傳錄音檔 (m4a / mp3 / wav)", type=["m4a","mp3","wav"], key=f"upload_{selected_word}")
    if uploaded:
        ext = uploaded.name.split('.')[-1]
        save_path = os.path.join(AUDIO_DIR, f"{selected_word.lower()}.{ext}")
        with open(save_path, 'wb') as f:
            f.write(uploaded.read())
        st.success(f"✅ 已儲存至 {save_path}")
        st.cache_data.clear()
        st.rerun()

    if audio_path:
        st.audio(audio_path)


# ════ 欄三：預覽 ════
with col_preview:
    st.markdown('<div class="card-title">👁️ 即時排版預覽</div>', unsafe_allow_html=True)

    preview_intonation = st.text_input(
        "語調 (直接修改預覽)",
        value=intonation,
        placeholder="e.g. 1..",
        key=f"into_preview_{selected_word}"
    )

    preview_bytes = render_matrix_preview(minum_str, preview_intonation)
    if preview_bytes:
        st.image(preview_bytes, caption="音標排版預覽", use_container_width=True)
    else:
        st.markdown(
            f'<div style="padding:20px; border:1px dashed #444; border-radius:8px; text-align:center; color:#666;">'
            f'🔤 音標：<code>{minum_str[:60]}</code><br><small>（預覽需載入音標資源）</small></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown('<div class="card-title">🚀 合成影片</div>', unsafe_allow_html=True)
    display_markers_final = st.session_state.get(f"rec_markers_{selected_word}", load_markers(selected_word))
    if audio_path and display_markers_final:
        if st.button("🎬 一鍵合成影片", type="primary", use_container_width=True, key=f"render_{selected_word}"):
            with st.spinner("⚙️ 合成中，請稍候..."):
                # 把 markers 的 ts 寫入 production_test.csv 並呼叫生產引擎
                try:
                    import subprocess
                    # 先把 markers 存一份 JSON
                    save_markers(selected_word, display_markers_final)
                    st.success("✅ 分鏡記錄已確認，正在觸發影片合成...")
                    result = subprocess.run(
                        [sys.executable, "production_master.py", "--word", selected_word],
                        capture_output=True, text=True, cwd=os.path.dirname(__file__)
                    )
                    if result.returncode == 0:
                        out_file = os.path.join(OUTPUT_DIR, f"{selected_word}_V5.3.mp4")
                        if os.path.exists(out_file):
                            st.video(out_file)
                        else:
                            st.info(result.stdout)
                    else:
                        st.error(result.stderr[:500])
                except Exception as e:
                    st.error(f"合成失敗：{e}")
    else:
        audio_icon   = "✅" if audio_path else "❌"
        markers_icon = "✅" if display_markers_final else "❌"
        st.caption(f"需要：{audio_icon} 已上傳音檔 + {markers_icon} 有分鏡時間軸記錄")


# ─── Footer ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#444; font-size:12px;">SoR Studio v1.0 · 700 單字智能錄影棚 · 由 Python + Streamlit 驅動</div>',
    unsafe_allow_html=True
)
