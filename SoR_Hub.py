import streamlit as st
import os
import json
import glob
import csv
import socket
from dotenv import load_dotenv
import platform

# 1. 載入全域金鑰
_env_path = "/Users/gray/Documents/python_project/.env"
if os.path.exists(_env_path):
    load_dotenv(_env_path)

# ── 1. 環境辨識 (自動切換本地/雲端) ───────────────────────────────────────────
import platform
hostname = socket.gethostname()
# 偵測是否在本地 (包含 Mac-mini 字樣、或作業系統為 Darwin 且路徑在 /Users 下)
IS_LOCAL = "Mac-mini" in hostname or "localhost" in hostname or (platform.system() == "Darwin" and "/Users/" in __file__)

# ── 2. 路徑設定 ──────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
YOUTUBEDB_DIR = os.path.join(BASE_DIR, "Systems_Data", "youtubedb")
SOR_EDU_DIR   = os.path.join(BASE_DIR, "SoR_Education")
PHONICS_DIR   = os.path.join(SOR_EDU_DIR, "sor_phonics_app")
STUDIO_DIR    = os.path.join(SOR_EDU_DIR, "Vocab_700") 
LINEBOT_DIR   = os.path.join(SOR_EDU_DIR, "sor_line_db_bot")
FOCUS_DIR     = os.path.join(SOR_EDU_DIR, "FocusGuardv1")
FOCUS_PRO_DIR = os.path.join(SOR_EDU_DIR, "FocusGuard_Parent_Pro")
LOGO_PATH     = os.path.join(PHONICS_DIR, "assets", "images", "sor_brain_logo.png")

# ── 3. 動態 URL 對照表 ───────────────────────────────────────────────────────
if IS_LOCAL:
    SERVER_URLS = {
        "phonics":   "http://localhost:5055",
        "studio":    "http://localhost:8501",
        "youtubedb": "http://localhost:8504",
        "linebot":   "http://localhost:5005",
        "king":      "http://localhost:8503",
        "song":      "http://localhost:5088",
        "focus":     "http://localhost:5099",
        "focus_pro": "http://localhost:5100",
        "official":  "https://www.milinguall.com",
    }
    MODE_LABEL = "🛠️ LOCAL DEV MODE"
else:
    SERVER_URLS = {
        "phonics":   "https://sor14.duckdns.org/phonics/?v=13",
        "studio":    "https://sor14.duckdns.org/studio",
        "youtubedb": "https://sor14.duckdns.org/youtubedb",
        "linebot":   "https://sor14.duckdns.org/linebot",
        "king":      "https://sor14.duckdns.org/king",
        "song":      "https://sor14.duckdns.org/song",
        "focus":     "https://sor14.duckdns.org/focus",
        "focus_pro": "https://sor14.duckdns.org/focus_pro",
        "official":  "https://www.milinguall.com",
    }
    MODE_LABEL = "🌍 PRODUCTION LIVE"

# ── 4. 頁面設定 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="蕭博士 SoR 美語 · 系統中樞",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 5. 品牌 CSS (完整復原華麗介面) ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
:root {
    --bg-main: #FDFCFB; --bg-card: #FFFFFF; --border: #EAE4DC;
    --text-dark: #1A1A2E; --text-light: #A0A0B8;
    --accent-warm: #E8896A; --accent-blue: #4AABDB; --accent-green: #2E8B5A;
    --accent-purple: #7B4DC9; --shadow-sm: 0 2px 12px rgba(30,30,60,0.06);
}
.stApp, .stApp > header { background-color: var(--bg-main); color: var(--text-dark); }
label, .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th { color: var(--text-dark) !important; }
.stat-chip { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 12px; padding: 0.75rem 1.4rem; text-align: center; flex: 1; box-shadow: var(--shadow-sm); }
.stat-chip .num { font-size: 1.8rem; font-weight: 900; background: linear-gradient(135deg, var(--accent-warm), var(--accent-blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stat-chip .lbl { font-size: 0.72rem; color: var(--text-light); margin-top: 0.3rem; font-weight: 500; }
.section-header { display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; font-weight: 700; color: #5A5A72; text-transform: uppercase; margin: 1rem 0; padding-bottom: 0.6rem; border-bottom: 1.5px solid var(--border); }
.module-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 18px; padding: 1.5rem; height: 100%; position: relative; transition: all 0.22s ease; box-shadow: var(--shadow-sm); }
.module-card:hover { transform: translateY(-4px); box-shadow: 0 8px 32px rgba(30,30,60,0.1); border-color: var(--accent-warm); }
.module-card h3 { color: var(--text-dark) !important; font-size: 1.15rem; font-weight: 800; margin: 0 0 0.5rem 0; }
.module-card p { color: #5A5A72 !important; font-size: 0.88rem; line-height: 1.6; margin: 0 0 0.8rem 0; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 0.8rem; }
.tag { font-size: 0.72rem; font-weight: 600; padding: 3px 10px; border-radius: 20px; background: #F0EEF8; color: #5A5A72; border: 1px solid #E2DFF0; }
.portal-btn { display: block; width: 100%; text-align: center; background: linear-gradient(135deg, var(--accent-warm), #D05E3A); color: white !important; text-decoration: none; border-radius: 10px; padding: 0.65rem; font-weight: 700; margin-top: auto; box-shadow: 0 3px 12px rgba(232, 137, 106, 0.3); transition: opacity 0.15s; }
.portal-btn:hover { opacity: 0.88; }
</style>
""", unsafe_allow_html=True)

# ── 6. 數據計算 ──────────────────────────────────────────────────────────────
yt_count = 0
try:
    with open(os.path.join(YOUTUBEDB_DIR, "data", "index.json"), "r", encoding="utf-8") as f:
        yt_count = len(json.load(f))
except: pass

phonics_count = 0
try:
    with open(os.path.join(PHONICS_DIR, "Cleaned_Phonetic_Dictionary.csv"), "r", encoding="utf-8") as f:
        phonics_count = max(0, sum(1 for _ in csv.reader(f)) - 1)
except: pass

# ── 7. 頂部視覺 ──────────────────────────────────────────────────────────────
col_l, col_r = st.columns([8, 2])
with col_l:
    st.markdown(f"<h1>蕭博士 <span style='color:var(--accent-warm)'>SoR</span> 美語 · 系統中樞</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:var(--text-light)'>FoR you, FoR me, FoRmosa | {MODE_LABEL}</p>", unsafe_allow_html=True)

with col_r:
    st.markdown(f"<div style='text-align:right; padding-top:10px'><span style='background:linear-gradient(135deg,#E8896A,#D05E3A); color:white; padding:4px 12px; border-radius:20px; font-size:0.7rem; font-weight:700;'>HUB v1.3 LIVE</span></div>", unsafe_allow_html=True)

st.markdown("---")

# ── 8. 狀態列 ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
chips = [(c1, yt_count, "影片知識庫"), (c2, phonics_count if phonics_count else "4,000+", "音典收錄單字"), (c3, "700+", "製作室腳本"), (c4, "● 運行中", "AI 語音機器人"), (c5, "● 運行中", "Focus Guard")]
for col, val, lbl in chips:
    with col:
        st.markdown(f'<div class="stat-chip"><div class="num">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

# ── 9. 功能區 ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🚀 核心工具與說明書</div>', unsafe_allow_html=True)

st.markdown(f'''
<div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
    <h3 style="margin-top:0; color:#10b981; font-size:1.1rem;">📚 智慧互動語音說明書 (User Manual)</h3>
    <p style="margin-bottom:10px; font-size:0.95rem; color:var(--text-muted);">為老師與家長設計，內建 AI 語音助理，點擊「聽語音導覽」即可輕鬆了解所有系統的操作方式！</p>
    <a href="{SERVER_URLS["focus"]}/manual" class="portal-btn" style="background:linear-gradient(135deg,#10b981,#059669); display:inline-block; width:auto; padding:8px 20px;" target="_blank">🔊 開啟語音說明書</a>
</div>
''', unsafe_allow_html=True)

ca, cb, cc = st.columns(3)

with ca:
    st.markdown(f'''
    <div class="module-card" style="border-top:4px solid var(--accent-blue)">
        <h3>🔤 音典</h3>
        <p>SoR 七步驟互動教學介面。母音強調、音位垂直對齊、可調速語音播放。<br>帶孩子從「聽」到「認識」，每個步驟都有科學依據。</p>
        <div class="tag-row"><span class="tag">HTML · JS</span><span class="tag">Step 1-7</span><span class="tag">音位對齊</span></div>
        <a class="portal-btn" style="background:linear-gradient(135deg,var(--accent-blue),#2980b9)" href="{SERVER_URLS["phonics"]}">🚀 進入音典</a>
    </div>''', unsafe_allow_html=True)

with cb:
    st.markdown(f'''
    <div class="module-card" style="border-top:4px solid var(--accent-warm)">
        <h3>🎬 製作室</h3>
        <p>700 核心詞彙的影片自動化產線。錄影腳本生成、矩陣佈局、四排音標對齊、Live-Marker 自動打點。</p>
        <div class="tag-row"><span class="tag">Python</span><span class="tag">MoviePy</span><span class="tag">四排音標</span></div>
        <a class="portal-btn" href="{SERVER_URLS["studio"]}">🎬 進入製作室</a>
    </div>''', unsafe_allow_html=True)

with cc:
    st.markdown(f'''
    <div class="module-card" style="border-top:4px solid #e8508a">
        <h3>🎵 歌曲教材系統</h3>
        <p>AI 自動生成英文歌詞教學講義。SoR 專利音標空白框、翻譯底線、置換練習、Word Bank，可直接印出供學生手寫。</p>
        <div class="tag-row"><span class="tag">Flask</span><span class="tag">Gemini AI</span><span class="tag">列印優化</span></div>
        <a class="portal-btn" style="background:linear-gradient(135deg,#e8508a,#b5285a)" href="{SERVER_URLS["song"]}">🎵 進入歌曲教材</a>
    </div>''', unsafe_allow_html=True)

cd, ce = st.columns(2)
with cd:
    st.markdown(f'''
    <div class="module-card" style="border-top:4px solid var(--accent-green)">
        <h3>🔍 影片知識庫</h3>
        <p>影片採收、Whisper AI 語音轉錄、ChromaDB 語意搜尋。<br>將每支教學影片轉化為可被精準查詢的內容資產。</p>
        <div class="tag-row"><span class="tag">Streamlit</span><span class="tag">ChromaDB</span><span class="tag">Whisper AI</span></div>
        <a class="portal-btn" style="background:linear-gradient(135deg,var(--accent-green),#1a6b3f)" href="{SERVER_URLS["youtubedb"]}">🔍 進入知識庫</a>
    </div>''', unsafe_allow_html=True)

with ce:
    st.markdown(f'''
    <div class="module-card" style="border-top:4px solid var(--accent-purple)">
        <h3>👑 國中智慧王</h3>
        <p>學科競賽、猜歌遊戲、心算系統，多元互動教學平台。</p>
        <div class="tag-row"><span class="tag">Python</span><span class="tag">Flask</span><span class="tag">遊戲化</span></div>
        <a class="portal-btn" style="background:linear-gradient(135deg,var(--accent-purple),#5a35a0)" href="{SERVER_URLS["king"]}">👑 進入系統</a>
    </div>''', unsafe_allow_html=True)

st.markdown('<div class="section-header">🤖 AI 服務工具</div>', unsafe_allow_html=True)
ce, cf = st.columns(2)
with ce:
    st.markdown(f'''
    <div class="module-card" style="border-left:4px solid var(--accent-purple); border-radius:18px">
        <h3>🤖 LineOA 蕭博士 AI</h3>
        <p>蕭博士 AI 數位分身。家長在 LINE 提問，機器人以蕭博士的語氣與知識庫精準回答，支援語音互動。</p>
        <div class="tag-row"><span class="tag">Flask</span><span class="tag">Line API</span><span class="tag">GPT-4o</span></div>
        <a class="portal-btn" style="background:linear-gradient(135deg,#6c3fc5,#4a2d8a)" href="{SERVER_URLS["linebot"]}">⊙ 查看機器人狀態</a>
    </div>''', unsafe_allow_html=True)
with cf:
    st.markdown(f'''
    <div class="module-card" style="border-top:4px solid #f39c12">
        <h3>🛡️ Focus Guard Pro (家長版)</h3>
        <p><b>[最新發送]</b> 給所有家長的專業方案。具備 AI 審查、斷電記憶計時與影子守護，支援手機遠端遙控與 PIN 碼修改。</p>
        <div class="tag-row"><span class="tag">Pro Installer</span><span class="tag">AI Guard</span><span class="tag">遙控碼管理</span></div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
            <a class="portal-btn" style="background:linear-gradient(135deg,#f39c12,#d35400)" href="{SERVER_URLS["focus_pro"]}">🛡️ 進入控制台</a>
            <div style="display:flex; gap:4px;">
                <a class="portal-btn" style="background:linear-gradient(135deg,#64748b,#475569); box-shadow:none; flex:1; font-size:0.65rem; padding:8px 2px;" href="{SERVER_URLS["focus_pro"]}/FocusGuardPro_Mac.zip">🍎 Mac 版</a>
                <a class="portal-btn" style="background:linear-gradient(135deg,#34495e,#2c3e50); box-shadow:none; flex:1; font-size:0.65rem; padding:8px 2px;" href="{SERVER_URLS["focus_pro"]}/FocusGuardPro_Win.zip">🪟 Win 版</a>
            </div>
        </div>
    </div>''', unsafe_allow_html=True)

st.markdown('<div class="section-header">🏫 課程專案區 (Online Course Specific)</div>', unsafe_allow_html=True)
cx, cy = st.columns(2)
with cx:
    st.markdown(f'''
    <div class="module-card" style="border-left:4px solid #95a5a6">
        <h3>🎓 Focus Guard v1 (課程版)</h3>
        <p>針對線上課程設計，支援老師一鍵簽到、上課專注監控與基本 App 封鎖。</p>
        <div class="tag-row"><span class="tag">Legacy</span><span class="tag">學員管理</span></div>
        <a class="portal-btn" style="background:#7f8c8d" href="{SERVER_URLS["focus"]}">🚀 進入課程版面板</a>
    </div>''', unsafe_allow_html=True)

# ── 10. API Vault (金鑰金庫與系統地圖) ─────────────────────────────────────────
st.markdown("---")

import dotenv
env_file = os.path.join(BASE_DIR, ".env")
current_env = dotenv.dotenv_values(env_file) if os.path.exists(env_file) else {}

# 定義有哪些系統需要金鑰
SYSTEMS = [
    {"id": "LINEOA", "name": "🤖 LineOA 機器人", "desc": "對外服務與問答"},
    {"id": "SONG", "name": "🎵 歌曲教材產出", "desc": "負責爬蟲與排版"},
    {"id": "YOUTUBE", "name": "🔍 YouTube 知識庫", "desc": "處理文字向量化"},
    {"id": "BRAIN", "name": "🏭 蕭博士大腦工廠", "desc": "切割與清理 YouTube 逐字稿"},
    {"id": "DBTOQA", "name": "🧠 DBtoQA", "desc": "問答資料轉化器"},
]

# 讀取使用者新增的自訂模組
modules_file = os.path.join(BASE_DIR, "api_vault_modules.json")
if os.path.exists(modules_file):
    try:
        with open(modules_file, "r", encoding="utf-8") as f:
            custom_systems = json.load(f)
            SYSTEMS.extend(custom_systems)
    except: pass

PROVIDERS = ["OpenAI", "Google Gemini", "Anthropic", "DeepSeek", "OpenRouter"]

new_configs = {}

with st.expander("🔑 模組化 API Vault (展開設定金鑰與帳單管理)", expanded=False):
    st.markdown("將每個子系統使用的 AI 供應商獨立分開，方便未來能清楚計算各模組的使用費用（你可以在此設定不同的 Key 或共用同一把）。")
    
    # 表頭
    st.markdown('<div class="section-header" style="margin-bottom:0px; padding-bottom:0px; display:grid; grid-template-columns:1.2fr 1fr 1.5fr 1.5fr; gap:10px;"><span>子系統模組</span><span>AI 供應商</span><span>API Key 金鑰</span><span>指定模型 (Model Name)</span></div>', unsafe_allow_html=True)
    st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)
    
    # 動態生成表單
    for sys in SYSTEMS:
        c1, c2, c3, c4 = st.columns([1.2, 1, 1.5, 1.5])
        with c1:
            st.markdown(f"**{sys['name']}**<br><span style='font-size:0.8rem; color:var(--text-light)'>{sys['desc']}</span>", unsafe_allow_html=True)
        with c2:
            prev_provider = current_env.get(f"{sys['id']}_PROVIDER", "OpenAI")
            idx = PROVIDERS.index(prev_provider) if prev_provider in PROVIDERS else 0
            new_configs[f"{sys['id']}_PROVIDER"] = st.selectbox("PROVIDER", options=PROVIDERS, index=idx, key=f"sel_{sys['id']}", label_visibility="collapsed")
        with c3:
            # 尋找該模組是否有專屬金鑰，沒有的話試圖從早期的全局金鑰 fallback
            val = current_env.get(f"{sys['id']}_API_KEY", "")
            if not val:
                fallback_map = {
                    "OpenAI": "OPENAI_API_KEY",
                    "Google Gemini": "GOOGLE_API_KEY", 
                    "Anthropic": "ANTHROPIC_API_KEY",
                    "DeepSeek": "DEEPSEEK_API_KEY",
                    "OpenRouter": "OPENROUTER_API_KEY"
                }
                val = current_env.get(fallback_map.get(prev_provider, ""), "")
                
            new_configs[f"{sys['id']}_API_KEY"] = st.text_input("KEY", value=val, type="password", key=f"key_{sys['id']}", label_visibility="collapsed")
        with c4:
            new_configs[f"{sys['id']}_MODEL"] = st.text_input("MODEL", value=current_env.get(f"{sys['id']}_MODEL", ""), placeholder="如 gpt-4o", key=f"mod_{sys['id']}", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # 新增模組功能
with st.expander("➕ 新增其他自訂系統模組", expanded=False):
    col_add1, col_add2, col_add3 = st.columns(3)
    with col_add1:
        new_mod_name = st.text_input("模組顯示名稱 (例如: 🧠 大腦工廠)", key="new_mod_name")
    with col_add2:
        new_mod_id = st.text_input("英文代號 (將作為變量前綴,如 BRAIN)", key="new_mod_id")
    with col_add3:
        new_mod_desc = st.text_input("簡短敘述", key="new_mod_desc")
    
    if st.button("加入自訂模組清單", use_container_width=True):
        if new_mod_name and new_mod_id:
            new_mod_id = new_mod_id.upper().strip().replace(" ", "_")
            new_item = {"id": new_mod_id, "name": new_mod_name, "desc": new_mod_desc}
            
            # 儲存
            curr_custom = []
            if os.path.exists(modules_file):
                try:
                    curr_custom = json.load(open(modules_file, "r", encoding="utf-8"))
                except: pass
            curr_custom.append(new_item)
            with open(modules_file, "w", encoding="utf-8") as f:
                json.dump(curr_custom, f, ensure_ascii=False, indent=4)
            st.rerun()

# 其他非通用 AI 的固定 API
st.markdown("---")
st.markdown("#### ⚙️ 其他核心服務金鑰")
c1, c2, c3, c4 = st.columns([1.2, 1, 1.5, 1.5])
with c1:
    st.markdown("**🎬 700單自動製片**<br><span style='font-size:0.8rem; color:var(--text-light)'>用於產生逼真人物語音的 D-ID API</span>", unsafe_allow_html=True)
with c2:
    st.markdown("<span style='display:inline-block; margin-top:5px; font-weight:bold; color:var(--text-light)'>D-ID 官方</span>", unsafe_allow_html=True)
with c3:
    new_configs["DID_API_KEY"] = st.text_input("KEY", value=current_env.get("DID_API_KEY", ""), type="password", key="key_did", label_visibility="collapsed")
with c4:
    st.markdown("<span style='display:inline-block; margin-top:8px; font-size:0.8rem; color:var(--text-light)'>固定微服務，無需選模型</span>", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
if st.button("💾 將上述分配結果儲存至 `.env` 並生效", use_container_width=True):
    for k, v in new_configs.items():
        dotenv.set_key(env_file, k, v)
    load_dotenv(env_file, override=True)
    st.success("✅ `.env` 已依據模組分離架構更新完畢！")
    st.rerun()

# ── 11. 開發者發佈工具 (僅地端顯示) ──────────────────────────────────────────
if IS_LOCAL:
    import subprocess
    st.markdown("---")
    st.markdown('<div class="section-header" style="color:var(--accent-warm)">🛠️ 開發與部署工具 (DEV & DEPLOY)</div>', unsafe_allow_html=True)
    with st.expander("🚀 專案一鍵上傳伺服器 (Git + Rsync)", expanded=True):
        st.write("這個功能會自動打包目前所有的進度，同時備份到 Git 雲端，並使用 `deploy.sh` 覆蓋到 Hetzner 伺服器上。")
        
        # ── 自動偵測修改了哪些檔案來當作預設備註 ──
        default_msg = "Auto upload & update from SoR Hub"
        try:
            status_res = subprocess.run(["git", "status", "-s"], cwd=BASE_DIR, capture_output=True, text=True)
            changed_files = [line.strip().split()[-1] for line in status_res.stdout.split('\n') if line.strip()]
            if changed_files:
                file_names = [os.path.basename(f) for f in changed_files]
                if len(file_names) <= 3:
                    default_msg = f"Update {', '.join(file_names)}"
                else:
                    default_msg = f"Update {file_names[0]} and {len(file_names)-1} other files"
        except Exception:
            pass

        commit_msg = st.text_input("本次更新備註 (Git Commit Message)：", value=default_msg)
        
        if st.button("🔥 確認執行上傳", use_container_width=True):
            with st.spinner("正在進行 Git 打包與伺服器同步，請稍候..."):
                try:
                    logs = []
                    # 1. Git Add
                    subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
                    logs.append("✔ Git 檔案加入完成 (git add .)")
                    
                    # 2. Git Commit (檢查是否有變更)
                    status_check = subprocess.run(["git", "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True)
                    if status_check.stdout.strip():
                        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=True)
                        logs.append(f'✔ Git 建立版本 ({commit_msg})')
                    else:
                        logs.append("ℹ 無檔案變更，跳過 Git Commit")
                    
                    # 3. Git Push
                    push_res = subprocess.run(["git", "push"], cwd=BASE_DIR, capture_output=True, text=True)
                    if push_res.returncode != 0:
                        st.error(f"❌ Git Push 失敗，請檢查網路或衝突：\n{push_res.stderr}")
                        st.stop()
                    logs.append("✔ Git 推送雲端完成 (git push)")
                    
                    # 4. 執行 deploy.sh (Rsync)
                    deploy_sh_path = os.path.join(BASE_DIR, "deploy.sh")
                    deploy_res = subprocess.run(["bash", deploy_sh_path], cwd=BASE_DIR, capture_output=True, text=True)
                    if deploy_res.returncode != 0:
                        st.error(f"❌ 伺服器同步 (Deploy) 失敗：\n{deploy_res.stderr}")
                        st.stop()
                    logs.append("✔ 伺服器同步與服務重啟完成 (deploy.sh)")
                    
                    st.success("🎉 大一統發布成功！所有修改皆已送達正式伺服器。")
                    with st.expander("查看執行詳情與日誌"):
                        st.markdown("### 執行進度")
                        st.code("\n".join(logs))
                        st.markdown("### Git Push 詳細日誌")
                        st.code(push_res.stdout + push_res.stderr)
                        st.markdown("### Deploy 詳細日誌")
                        st.code(deploy_res.stdout)
                except Exception as e:
                    st.error(f"❌ 部署過程中發生非預期錯誤：\n{str(e)}")
