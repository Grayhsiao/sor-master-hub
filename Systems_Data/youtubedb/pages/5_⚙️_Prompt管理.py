import streamlit as st
import sys, os, json, random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="Prompt 管理 · 蕭博士 SoR", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(168,85,247,0.25);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p  { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }

/* 拔除 Streamlit 預設的巨大左右間距與最大寬度限制 */
[data-testid="block-container"] { 
    padding-left: 2rem !important; 
    padding-right: 2rem !important; 
    max-width: none !important; 
    width: 100% !important;
}

/* 流程步驟 */
.flow-bar {
    display: flex; align-items: center; gap: 0.5rem;
    background: rgba(22,27,34,0.8); border-radius: 12px;
    padding: 0.8rem 1.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(48,54,61,0.6); font-size: 0.85rem;
}
.flow-step { color: #00C37A; font-weight: 600; }
.flow-arrow { color: rgba(230,237,243,0.3); }
.flow-inactive { color: rgba(230,237,243,0.4); }

/* Prompt 卡片 */
.p-card {
    border-radius: 14px; padding: 1.1rem 1.3rem; margin-bottom: 0.5rem;
    transition: all 0.2s; position: relative;
}
.p-card-sel  { background: rgba(30,10,60,0.9); border: 2px solid #a855f7; box-shadow: 0 0 20px rgba(168,85,247,0.18); }
.p-card-norm { background: rgba(22,27,34,0.9); border: 1px solid rgba(48,54,61,0.7); }
.p-card:hover { border-color: rgba(168,85,247,0.5) !important; }
.p-name { font-weight: 600; font-size: 0.93rem; color: #E6EDF3; }
.p-desc { font-size: 0.79rem; color: rgba(230,237,243,0.5); margin-top: 0.3rem; line-height: 1.5; }
.badge {
    display: inline-block; border-radius: 20px; padding: 0.1rem 0.55rem;
    font-size: 0.68rem; font-weight: 700; margin-left: 0.4rem; vertical-align: middle;
}
.badge-default { background: rgba(0,195,122,0.15); border: 1px solid rgba(0,195,122,0.4); color: #00C37A; }
.badge-locked  { background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.4); color: #818cf8; }
.badge-custom  { background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; }

/* 預覽區塊 */
.preview-box {
    background: rgba(15,18,25,0.95); border: 1px solid rgba(48,54,61,0.7);
    border-radius: 12px; padding: 1.2rem 1.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.79rem; line-height: 1.75; color: rgba(230,237,243,0.8);
    white-space: pre-wrap; max-height: 400px; overflow-y: auto;
}
.preview-header {
    font-size: 0.78rem; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; margin-bottom: 0.6rem;
    padding-bottom: 0.4rem; border-bottom: 1px solid rgba(48,54,61,0.6);
}
.ph-prompt { color: #818cf8; }
.ph-format { color: #00C37A;  }

/* 平台標籤 */
.plat-tab {
    display: inline-block; border-radius: 8px; padding: 0.3rem 0.8rem;
    font-size: 0.78rem; font-weight: 600; margin: 0.2rem; cursor: pointer;
}
.plat-line   { background: rgba(0,195,122,0.12); color: #00C37A; border: 1px solid rgba(0,195,122,0.3); }
.plat-thread { background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.3); }
.plat-notion { background: rgba(255,255,255,0.07); color: #E6EDF3; border: 1px solid rgba(255,255,255,0.15); }
.plat-fb     { background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }

section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)

# ── 側邊欄 ────────────────────────────────────────────────────────────────────

# ── 標題 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>⚙️ Prompt 管理 — Step 1</h1>
    <p>設定 AI 規則 + 輸出格式。設定完成後，前往「文案精煉」產生內容，再到「行銷素材」套用格式輸出。</p>
</div>
""", unsafe_allow_html=True)

# 流程提示
st.markdown("""
<div class="flow-bar">
    <span class="flow-step">⚙️ Step 1 設定規則（你在這裡）</span>
    <span class="flow-arrow">──►</span>
    <span class="flow-inactive">✨ Step 2 文案精煉（丟素材生成內容）</span>
    <span class="flow-arrow">──►</span>
    <span class="flow-inactive">🚀 Step 3 行銷素材（套格式輸出）</span>
</div>
""", unsafe_allow_html=True)

# ── 載入資料 ──────────────────────────────────────────────────────────────────
try:
    from utils import load_prompts, generate_sor_stream
    prompts = load_prompts()
    PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "prompts.json")
except Exception as e:
    st.error(f"❌ 無法載入：{e}"); st.stop()

# ── Session State ─────────────────────────────────────────────────────────────
if "sel_id"  not in st.session_state:
    st.session_state.sel_id = next((p["id"] for p in prompts if p.get("is_default")), prompts[0]["id"])
if "rand_seed" not in st.session_state:
    st.session_state.rand_seed = random.randint(0, 9999)

# 逐字稿範例庫（6篇，隨機抽）
EXAMPLES = [
    {"title": "背單字背了就忘？大腦記憶機制大揭秘",
     "text": "蕭博士今天要跟大家講一個很多家長都會踩的地雷。就是讓小孩背單字。你有沒有這個經驗？小孩今天背，明天就忘了。你很挫折，小孩更挫折。問題出在哪裡？問題出在大腦根本沒有「背單字這件事」。大腦只有「記住情境」這件事。你要讓單字跟情境連結，跟聲音連結，跟造句連結。光看字你的大腦沒有施力點。就像你要把釘子打進牆壁，你不能用手指頭戳，你要用鐵鎚。聲音就是你的鐵鎚。"},
    {"title": "PA 音素覺察是英語閱讀的DNA",
     "text": "今天來講 PA，phonological awareness，音素覺察。這個是所有英語閱讀能力的根基。台灣的孩子學英文最大的問題是什麼？就是沒有 PA。我們學注音，所以我們知道中文怎麼拼音。但英文你要知道 cat 是三個音素，c-a-t。很多孩子眼睛看到 cat，他不知道這個字有幾個聲音。這就是為什麼他一直記不住。大腦需要聲音當鉤子把意義掛上去，沒有鉤子，意義就掉了。"},
    {"title": "為什麼補習補六年英文還是不會？",
     "text": "家長最常問我這個問題：我孩子補習補了六年，怎麼還是不會英文？答案很簡單，因為你在補的是翻譯，不是英文。你補翻譯，大腦就走翻譯這條路。中文→英文→中文，繞一圈。SoR 要做的是直接讓英文跟意義連接，不要中文當中間人。就像你學游泳，你不是先學游泳理論然後再下水，你直接下水。語言也是一樣，要在情境裡面學，要大量輸入。"},
    {"title": "閱讀流暢性：為什麼孩子念英文磕磕巴巴？",
     "text": "今天講閱讀流暢性的問題。很多孩子看到英文字，要一個一個字去拼，這就是解碼能力不夠。解碼就是看到字形，直接對應到聲音。像我們看到「的」，不需要把注音唸出來，直接就知道是「的」。這個過程叫做自動化。英文的自動化要靠大量重複閱讀同樣的材料。七次法則。同一篇文章讀七遍，你的大腦才會把這條路鋪平，變成高速公路。"},
    {"title": "自然發音法 vs KK音標，哪個對？",
     "text": "這個問題我被問了幾百次了。自然發音法好還是KK音標好？答案是：這是個假問題。真正的問題是你要讓孩子的耳朵先學會。先聽，大量聽，聽到自然會說。自然發音法是讓孩子看到字就能發音的工具，不是學英語的起點。KK音標也一樣。會開車的人不需要先學懂引擎原理。你先會開，開熟了，有興趣再去研究。"},
    {"title": "SoR 的三個關鍵：Sound, Context, Repetition",
     "text": "今天講 SoR 的核心原則：Sound、Context、Repetition。Sound 聲音——任何語言學習都從聲音開始，不是從眼睛開始。Context 情境——單字要長在句子裡，句子要長在故事裡。Repetition 重複——大腦要七次才能製造穩固的神經連結。這三個缺一不可。你只給Sound沒有Context，孩子知道發音但不知道用法。只給Repetition沒有Sound，就是死背，背完就忘。"},
]

random.seed(st.session_state.rand_seed)
example = random.choice(EXAMPLES)

# ════════════════════════════════════════════════════════════
# 主佈局 (改為上下排版)
# ════════════════════════════════════════════════════════════
# ── 左欄：Prompt 版本選擇 ─────────────────────────────────
col_left, col_right = st.columns([1, 3], gap="large")

with col_left:
    st.markdown("#### 📚 選擇版本")
    st.caption("點卡片切換。🔒 原版唯讀，✏️ 自訂版可修改。")
    if st.button("⭐ 將此版設為預設", use_container_width=True):
        for p in prompts:
            p["is_default"] = (p["id"] == st.session_state.sel_id)
        with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        st.success("✅ 已更新預設")
        st.rerun()

    for p in prompts:
        is_sel  = st.session_state.sel_id == p["id"]
        locked  = p.get("locked", False)
        is_def  = p.get("is_default", False)

        badges = ""
        if is_def:  badges += ' <span class="badge badge-default">預設</span>'
        if locked:  badges += ' <span class="badge badge-locked">🔒 原版</span>'
        if not locked and not is_def: badges += ' <span class="badge badge-custom">✏️ 可改</span>'

        card_cls = "p-card-sel" if is_sel else "p-card-norm"
        st.markdown(f"""
        <div class="p-card {card_cls}">
            <div class="p-name">{p['name']}{badges}</div>
            <div class="p-desc">{p['description']}</div>
        </div>""", unsafe_allow_html=True)

        # 改成實體按鈕，不再用隱形疊加魔法，徹底解決黑框問題
        if not is_sel:
            if st.button(f"選擇 {p['name']}", key=f"sel_{p['id']}", use_container_width=True):
                st.session_state.sel_id = p["id"]
                st.rerun()
        else:
            st.button("✅ 目前選取", key=f"sel_{p['id']}", disabled=True, use_container_width=True)

    st.markdown("---")
with col_right:
# ── 右欄：三個主要 Tab ────────────────────────────────────
    current = next((p for p in prompts if p["id"] == st.session_state.sel_id), prompts[0])
    is_locked = current.get("locked", False)

    tab_prompt, tab_format, tab_test = st.tabs(
        ["✏️ Prompt 設定 & 預覽", "🎨 輸出格式設定 & 預覽", "🧪 即時測試"]
    )

    # ══════════════════════════════════════════════════════
    # Tab 1：Prompt 設定 + 預覽
    # ══════════════════════════════════════════════════════
    with tab_prompt:
        if is_locked:
            st.info("🔒 這是原版（唯讀）。若要修改，請切換到「我的自訂版」。")
            st.markdown(f"""<div class="preview-header ph-prompt">📋 PROMPT 原文（唯讀）</div>
            <div class="preview-box">{current.get('template','')}</div>""",
            unsafe_allow_html=True)
        else:
            st.markdown(f"**編輯：{current['name']}**")
            st.caption("保留 `{title}` 和 `{transcript}` 佔位符")
            edited_tmpl = st.text_area("Prompt", value=current.get("template",""),
                                       height=300, label_visibility="collapsed")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 儲存", type="primary", use_container_width=True):
                    for p in prompts:
                        if p["id"] == current["id"]:
                            p["template"] = edited_tmpl
                    with open(PROMPTS_PATH,"w",encoding="utf-8") as f:
                        json.dump(prompts, f, ensure_ascii=False, indent=2)
                    st.success("✅ 已儲存"); st.rerun()
            with c2:
                if st.button("↩️ 還原", use_container_width=True): st.rerun()

        # ── Prompt 預覽（填入範例後的實際樣子）──────────────
        st.markdown("---")
        st.markdown("**🔍 Prompt 預覽** — 填入範例後，AI 實際收到的完整內容")
    
        _, c_btn = st.columns([4, 1])
        with c_btn:
            if st.button("🔀 換例子 (隨機抽)", key="reload_p", use_container_width=True):
                st.session_state.rand_seed = random.randint(0, 9999)
                st.rerun()

        tmpl = current.get("template","")
        filled = tmpl.replace("{title}", example["title"]).replace("{transcript}", example["text"])
        st.markdown(f'<div class="preview-header ph-prompt">📋 PROMPT PREVIEW — 範例：{example["title"]}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="preview-box">{filled}</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # Tab 2：輸出格式設定 + 預覽
    # ══════════════════════════════════════════════════════
    with tab_format:
        st.markdown("**🎨 輸出格式設定**")
        st.caption("用自然語言描述每個平台的格式要求，儲存後會在「行銷素材」頁自動套用。")

        platform_labels = {
            "line_oa": ("💬 LINE OA", "plat-line"),
            "threads": ("🐦 Threads", "plat-thread"),
            "notion":  ("📓 Notion",  "plat-notion"),
            "fb":      ("📘 Facebook","plat-fb"),
        }

        fmt_settings = current.get("output_format_setting", {})
        new_settings = {}

        c_l, c_r = st.columns(2)
        pairs = list(platform_labels.items())
        for i, (key, (label, _)) in enumerate(pairs):
            col = c_l if i % 2 == 0 else c_r
            with col:
                new_settings[key] = st.text_area(
                    label, value=fmt_settings.get(key, ""),
                    height=100, key=f"fmt_{key}",
                    placeholder="例如：只要比喻外殼+3組Q&A，字數500字以內，結尾加hashtag"
                )

        if not is_locked:
            if st.button("💾 儲存格式設定", type="primary", use_container_width=True):
                for p in prompts:
                    if p["id"] == current["id"]:
                        p["output_format_setting"] = new_settings
                with open(PROMPTS_PATH,"w",encoding="utf-8") as f:
                    json.dump(prompts, f, ensure_ascii=False, indent=2)
                st.success("✅ 格式設定已儲存"); st.rerun()
        else:
            st.info("🔒 原版格式設定唯讀。切換到「我的自訂版」可修改。")

        # ── 格式輸出預覽 ───────────────────────────────────
        st.markdown("---")
        st.markdown("**🔍 格式輸出預覽** — 套用格式後，各平台的輸出大概長這樣")

        _, c_btn2 = st.columns([4, 1])
        with c_btn2:
            if st.button("🔀 換例子 (隨機抽)", key="reload_f", use_container_width=True):
                st.session_state.rand_seed = random.randint(0, 9999)
                st.rerun()

        # 模擬完整版 AI 輸出（靜態示意，不真的呼叫 AI）
        mock_output = f"""【理論背景（科學靈魂）】
    大腦記憶機制依賴神經連結（Synaptic Connections）。學習英文單字若僅依賴視覺死背，大腦缺乏施力點。根據 SRC 原則（Sound-Context-Repetition），聲音是記憶的鐵鎚，情境是鉤子，重複是固化的關鍵。

    【優化觀念（比喻外殼）】
    背單字就像打釘子——你不能用手指頭戳，你要用鐵鎚。聲音就是鐵鎚，造句是你在牆上找到的力點。沒有聲音的單字，就像沒有鐵鎚的釘子，再用力也只是徒勞。

    【實戰 Q&A（示意）】
    Q: 孩子今天背，明天就忘，怎麼辦？
    A: 因為沒有「聲音＋情境」這兩根支柱。讓孩子大聲造句，而不是看字默背。
    Q: 補習班死背單字法有效嗎？
    A: 對大腦來說，沒有聲音和情境的單字等於沒有鉤子的掛勾，意義掛不上去。"""

        # 依平台格式說明做簡單的模擬裁切
        platform_previews = {
            "line_oa": mock_output,
            "threads": "🎓 " + example["title"] + "\n\n「背單字就像打釘子——聲音才是鐵鎚。」\n\n完整教學 👉 連結 \n\n#蕭博士 #SoR #英文學習",
            "notion":  f"## {example['title']}\n\n### 理論背景\n大腦記憶機制依賴神經連結...\n\n### 優化觀念\n背單字就像打釘子...\n\n### Q&A\n1. Q: 孩子今天背明天忘？\n   A: 缺少聲音與情境...",
            "fb":      "👩‍👧 各位家長，你有沒有發現孩子背了就忘？\n\n蕭博士說：「背單字就像打釘子，沒有聲音這個鐵鎚，怎麼用力都打不進去。」\n\nQ: 補習六年還是不會怎麼辦？\nA: 你補的是翻譯不是英文，讓孩子先聽再說。\n\n#蕭博士 #英文教育",
        }

        for key, (label, css_cls) in platform_labels.items():
            fmt_desc = new_settings.get(key) or fmt_settings.get(key, "（未設定）")
            prev_text = platform_previews.get(key, "")
            with st.expander(f"{label} 預覽", expanded=(key=="line_oa")):
                st.caption(f"📋 格式要求：{fmt_desc}")
                st.markdown(f'<div class="preview-box">{prev_text}</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # Tab 3：即時測試（多模型並排串流）
    # ══════════════════════════════════════════════════════
    with tab_test:
        c_hd, c_rld = st.columns([4,1])
        with c_hd:
            st.markdown(f"**📄 範例逐字稿（隨機）**")
        with c_rld:
            if st.button("🔀 隨機換篇", use_container_width=True, key="reload_t"):
                st.session_state.rand_seed = random.randint(0, 9999)
                st.rerun()

        test_title = st.text_input("影片標題", value=example["title"])
        test_tx    = st.text_area("逐字稿", value=example["text"], height=140)

        st.markdown("---")
        st.markdown("**🤖 選擇比較模型**")
        cm1, cm2 = st.columns(2)
        with cm1: use_gpt = st.toggle("GPT-4o", value=True)
        with cm2: use_gem = st.toggle("Gemini", value=False)

        active = []
        if use_gpt: active.append(("gpt-4o","🟢 GPT-4o"))
        if use_gem: active.append(("gemini","🔵 Gemini"))

        if not active:
            st.info("請至少選一個模型")

        if st.button("🧪 開始測試", type="primary", use_container_width=True,
                     disabled=(not active or not test_tx.strip())):
            rcols = st.columns(len(active))
            for col, (model_key, model_label) in zip(rcols, active):
                with col:
                    st.markdown(f"**{model_label}**")
                    box = st.empty()
                    full = ""
                    try:
                        for chunk in generate_sor_stream(
                            test_title, test_tx, model_key,
                            custom_prompt=current.get("template") or None
                        ):
                            full += chunk
                            box.markdown(f'<div class="preview-box">{full}▌</div>',
                                         unsafe_allow_html=True)
                        box.markdown(f'<div class="preview-box">{full}</div>',
                                     unsafe_allow_html=True)
                    except Exception as e:
                        box.error(f"❌ {e}")
                    if full:
                        st.download_button("⬇️ 下載", full,
                                           file_name=f"result_{model_key}.txt",
                                           key=f"dl_{model_key}")
