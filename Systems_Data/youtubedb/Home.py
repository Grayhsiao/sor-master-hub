import streamlit as st
import sys
import os

# ── 確保 core/ 可被 import ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

st.set_page_config(
    page_title="蕭博士 SoR 內容工廠",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自訂 CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans TC', 'Inter', sans-serif;
}

/* Hero 區塊 */
.hero-container {
    background: linear-gradient(135deg, #0a3d2e 0%, #0D1117 50%, #1a0a3d 100%);
    border-radius: 20px;
    padding: 3rem 3rem 2.5rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(0, 195, 122, 0.2);
    position: relative;
    overflow: hidden;
}
.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 40%, rgba(0,195,122,0.07) 0%, transparent 50%),
                radial-gradient(circle at 70% 60%, rgba(99,102,241,0.07) 0%, transparent 50%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00C37A, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem;
    line-height: 1.2;
}
.hero-subtitle {
    color: rgba(230, 237, 243, 0.7);
    font-size: 1.1rem;
    margin: 0;
    font-weight: 300;
}
.hero-badge {
    display: inline-block;
    background: rgba(0, 195, 122, 0.15);
    border: 1px solid rgba(0, 195, 122, 0.4);
    color: #00C37A;
    border-radius: 20px;
    padding: 0.2rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 500;
    margin-bottom: 1.2rem;
    letter-spacing: 0.5px;
}

/* 功能卡片 */
.feature-card {
    background: rgba(22, 27, 34, 0.95);
    border: 1px solid rgba(48, 54, 61, 0.8);
    border-radius: 16px;
    padding: 1.6rem;
    height: 100%;
    transition: all 0.25s ease;
    cursor: default;
    position: relative;
    overflow: hidden;
}
.feature-card:hover {
    border-color: rgba(0, 195, 122, 0.5);
    box-shadow: 0 0 30px rgba(0, 195, 122, 0.08);
    transform: translateY(-2px);
}
.feature-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 3px;
    background: var(--accent-color, linear-gradient(90deg, #00C37A, #6366f1));
    border-radius: 16px 16px 0 0;
}
.card-icon { font-size: 2rem; margin-bottom: 0.7rem; }
.card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #E6EDF3;
    margin: 0 0 0.5rem;
}
.card-desc {
    font-size: 0.88rem;
    color: rgba(230, 237, 243, 0.55);
    line-height: 1.6;
    margin: 0;
}
.card-tag {
    display: inline-block;
    margin-top: 1rem;
    font-size: 0.75rem;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    background: rgba(0, 195, 122, 0.12);
    color: #00C37A;
    font-weight: 500;
}

/* 狀態列 */
.stat-box {
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(48, 54, 61, 0.6);
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    text-align: center;
}
.stat-number {
    font-size: 1.8rem;
    font-weight: 700;
    color: #00C37A;
}
.stat-label {
    font-size: 0.8rem;
    color: rgba(230, 237, 243, 0.5);
    margin-top: 0.2rem;
}

/* 側邊欄 */
section[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid rgba(48, 54, 61, 0.6);
}
.sidebar-brand {
    padding: 1rem 0 0.5rem;
    font-weight: 700;
    font-size: 1.05rem;
    color: #00C37A;
    letter-spacing: 0.3px;
}
</style>
""", unsafe_allow_html=True)

# ── 側邊欄 ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("v2.0 · 2026-03")

# ── Hero 區塊 ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">🎓 Science of Reading 完整工作流</div>
    <div class="hero-title">蕭博士<br>內容生產工廠</div>
    <p class="hero-subtitle">從 YouTube 影片到行銷素材，全自動化的知識轉化系統。<br>採收 → 轉錄 → 分析 → 精煉 → 發布，一站搞定。</p>
</div>
""", unsafe_allow_html=True)

# ── 系統狀態 ───────────────────────────────────────────────────────────────────
st.markdown("#### 📊 系統狀態")

# 讀取簡易狀態
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
    from config import SOURCE_DIR, DB_PATH, INDEX_FILE
    import json, glob

    srt_count = len(glob.glob(os.path.join(SOURCE_DIR, "*.srt")))
    txt_count = len([f for f in glob.glob(os.path.join(SOURCE_DIR, "*.txt"))
                     if not f.endswith("_strategy.txt")])
    strategy_count = len(glob.glob(os.path.join(SOURCE_DIR, "*_strategy.txt")))

    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        video_count = len(index_data)
    except Exception:
        video_count = 0

    db_ok = os.path.exists(DB_PATH)

except Exception:
    srt_count = txt_count = strategy_count = video_count = 0
    db_ok = False

c1, c2, c3, c4, c5 = st.columns(5)
stats = [
    (c1, str(video_count), "已索引影片"),
    (c2, str(srt_count), "字幕檔 (.srt)"),
    (c3, str(txt_count), "文字來源 (.txt)"),
    (c4, str(strategy_count), "SoR 策略文案"),
    (c5, "✅" if db_ok else "❌", "向量資料庫"),
]
for col, number, label in stats:
    with col:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{number}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 功能卡片 ───────────────────────────────────────────────────────────────────
st.markdown("#### 🚀 功能模組")

cards = [
    {
        "icon": "🎬",
        "title": "YouTube 採收",
        "desc": "貼入 YouTube 網址或播放清單，自動下載影片、Whisper 轉錄逐字稿，一鍵完成。",
        "tag": "yt-dlp · Whisper",
        "page": "pages/1_🎬_YouTube採收.py"
    },
    {
        "icon": "📚",
        "title": "知識庫搜尋",
        "desc": "跨影片 AI 語意搜尋，直接跳到影片對應時間點播放，快速找到關鍵知識。",
        "tag": "ChromaDB · Sentence Transformer",
        "page": "pages/2_📚_知識庫搜尋.py"
    },
    {
        "icon": "✨",
        "title": "文案精煉",
        "desc": "將逐字稿拆解成觀念結構，自動生成 Q&A 知識庫，也可互動式修改優化文案。",
        "tag": "GPT-4o · content_refinery",
        "page": "pages/3_✨_文案精煉.py"
    },
    {
        "icon": "📁",
        "title": "本地影片處理",
        "desc": "處理外接硬碟或本機資料夾中的影片檔。提取音訊 → Whisper 轉錄 → SoR 策略生成。",
        "tag": "FFmpeg · Whisper · Gemini",
        "page": "pages/6_📁_本地影片處理.py"
    },
    {
        "icon": "📱",
        "title": "Facebook 採收",
        "desc": "自動化 FB 貼文採收器。開啟瀏覽器後，經手動登入即可透過滾動頁面自動存檔。",
        "tag": "Selenium · Chrome",
        "page": "pages/7_📱_Facebook採收.py"
    },
]

# 顯示功能卡片，每 3 個分一行（為了顯示完整描述，3 欄比 4 欄更易讀）
for i in range(0, len(cards), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(cards):
            card = cards[i + j]
            with cols[j]:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="card-icon">{card['icon']}</div>
                    <div class="card-title">{card['title']}</div>
                    <p class="card-desc">{card['desc']}</p>
                    <span class="card-tag">{card['tag']}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.page_link(card["page"], label=f"前往 {card['title']} →")

# ── 工作流程圖 ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 🔄 完整工作流程")

st.markdown("""
```
YouTube / 本機音檔
        │
        ▼
   🎬 YouTube採收頁
  (yt-dlp + Whisper)
        │
        ├──► 字幕檔 (.srt) ──► 📚 知識庫搜尋
        │                     (ChromaDB 向量搜尋)
        │
        ▼
   ✨ 文案精煉頁
  (GPT-4o 結構分析)
        │
        ├──► Q&A 知識庫 (.txt)
        │
        ▼
   🚀 行銷素材頁
  (自動生成多平台素材)
        │
        ├──► LINE Flex Message
        ├──► Threads 貼文
        └──► LINE OA 廣播稿
```
""")
