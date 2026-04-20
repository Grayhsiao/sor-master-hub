import streamlit as st
import sys
import os
import json
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="行銷素材 · 蕭博士 SoR", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1a0a3d 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(139,92,246,0.25);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }
.asset-card {
    background: rgba(22,27,34,0.95); border: 1px solid rgba(48,54,61,0.8);
    border-radius: 14px; padding: 1.4rem; margin-bottom: 1.2rem;
}
.asset-header {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 1rem; font-weight: 600; color: #E6EDF3; margin-bottom: 0.8rem;
}
.platform-badge {
    display: inline-block; border-radius: 12px; padding: 0.2rem 0.7rem;
    font-size: 0.75rem; font-weight: 600;
}
.badge-line { background: rgba(0,195,122,0.15); color: #00C37A; }
.badge-threads { background: rgba(99,102,241,0.15); color: #818cf8; }
.badge-lineoa { background: rgba(251,191,36,0.15); color: #fbbf24; }
section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="page-header">
    <h1>🚀 行銷素材生成 — Step 3</h1>
    <p>選擇 Step 2 產出的策略文案，系統會依照你在 Step 1 設定的「平台輸出格式」自動排版產生最終貼文。</p>
</div>
""", unsafe_allow_html=True)

# 流程提示
st.markdown("""
<div class="flow-bar">
    <span class="flow-inactive">⚙️ Step 1 設定規則</span>
    <span class="flow-arrow">──►</span>
    <span class="flow-inactive">✨ Step 2 文案精煉</span>
    <span class="flow-arrow">──►</span>
    <span class="flow-step">🚀 Step 3 行銷素材（你在這裡）</span>
</div>
""", unsafe_allow_html=True)

# ── 載入 Step 1 設定的格式 ──────────────────────────────────────────────────
try:
    from core.utils import load_prompts
    prompts = load_prompts()
    default_p = next((p for p in prompts if p.get("is_default")), prompts[0])
    format_settings = default_p.get("output_format_setting", {})
except Exception as e:
    st.error(f"無法載入 Prompt 設定：{e}")
    format_settings = {}
    default_p = None

if default_p:
    st.info(f"💡 目前套用的格式來自 Prompt：**{default_p['name']}**")

# ── 載入可用影片清單 ───────────────────────────────────────────────────────────
try:
    from core.config import SOURCE_DIR, INDEX_FILE
    strategy_files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*_strategy.txt")))

    if not strategy_files:
        st.warning("⚠️ 尚無影片的策略文案，請先至「Step 2 文案精煉」生成策略文案。")
        st.stop()

    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            video_map = json.load(f)
        srt_to_id = video_map
    except Exception:
        srt_to_id = {}

    strategy_names = [os.path.basename(f) for f in strategy_files]
    display_names = [n.replace("_strategy.txt", "") for n in strategy_names]

except Exception as e:
    st.error(f"❌ 無法讀取資料：{e}")
    st.stop()

# ── 選擇影片 ──────────────────────────────────────────────────────────────────
st.markdown("#### 🎯 選擇素材檔案")
selected_idx = st.selectbox(
    "選擇要生成行銷素材的影片",
    range(len(display_names)),
    format_func=lambda i: display_names[i],
    label_visibility="collapsed"
)

selected_strategy_path = strategy_files[selected_idx]
selected_name = display_names[selected_idx]

video_id = None
srt_name = selected_name + ".srt"
if srt_name in srt_to_id:
    video_id = srt_to_id[srt_name]
else:
    for srt, vid in srt_to_id.items():
        if srt.replace(".srt", "") in selected_name or selected_name in srt.replace(".srt", ""):
            video_id = vid
            break

with st.expander("📖 查看文案原文 (Step 2 產出)"):
    with open(selected_strategy_path, "r", encoding="utf-8") as f:
        strategy_content = f.read()
    st.markdown(strategy_content)

st.markdown("---")

# ── 生成按鈕 ──────────────────────────────────────────────────────────────────
st.markdown("#### 🤖 AI 排版輸出設定")
model_choice = st.selectbox("選擇 AI 模型", ["gpt-4o", "gemini"])

col_btn, col_info = st.columns([2, 3])
with col_btn:
    generate_all = st.button("🚀 依設定格式生成全平台素材", type="primary", use_container_width=True)
with col_info:
    st.markdown("將生成：**LINE Flex JSON** · **Threads 貼文** · **LINE OA 廣播稿**")
    if video_id:
        st.caption(f"🔗 影片 ID：`{video_id}`")

if generate_all:
    with st.spinner("🚀 AI 正在依據 Step 1 的格式設定排版中..."):
        try:
            from core.export_marketing_assets import MarketingEngine
            from core.config import SOURCE_DIR
            from core.utils import openai_client, genai_client

            engine = MarketingEngine()
            parsed = engine.parse_strategy(strategy_content)
            vid_id = video_id or "unknown"
            title = selected_name[:40]
            
            # Helper: 用 AI 套用格式要求
            def format_with_ai(platform_name, req_format, content):
                if not req_format.strip():
                    return f"（無 {platform_name} 的格式設定，請至 Step 1 設定）"
                
                sys_prompt = f"你是一個專業行銷小編。請嚴格根據以下【格式要求】，將提供的【來源文案】重新排版與改寫。注意字數與標題規定。\n\n【格式要求】：{req_format}"
                
                if "gpt" in model_choice.lower() and openai_client:
                    res = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"【來源文案】：\n{content}"}
                        ],
                        temperature=0.7
                    )
                    return res.choices[0].message.content
                elif genai_client:
                    prompt = sys_prompt + "\n\n【來源文案】：\n" + content
                    res = genai_client.models.generate_content(
                        model="gemini-2.0-flash", contents=prompt
                    )
                    return res.text
                return "AI Client error."

            # ── 呼叫 AI 依據自然語言格式重排 ──────────────────────
            with st.spinner("排版 LINE OA..."):
                lineoa_post = format_with_ai("LINE OA", format_settings.get("line_oa", ""), strategy_content)
            with st.spinner("排版 Threads..."):
                threads_post = format_with_ai("Threads", format_settings.get("threads", ""), strategy_content)
            
            # Flex JSON 依然用程式碼封裝比較穩定，但替換文案
            flex_json = engine.generate_line_flex(vid_id, title, parsed.get("metaphor", title))

            # 儲存
            out_dir = os.path.join(os.path.dirname(SOURCE_DIR), "marketing_assets")
            os.makedirs(out_dir, exist_ok=True)

            flex_path    = os.path.join(out_dir, f"flex_lineoa_{vid_id}.json")
            threads_path = os.path.join(out_dir, f"post_threads_{vid_id}.txt")
            lineoa_path  = os.path.join(out_dir, f"post_lineoa_{vid_id}.txt")

            with open(flex_path, "w", encoding="utf-8") as f:
                json.dump(flex_json, f, ensure_ascii=False, indent=2)
            with open(threads_path, "w", encoding="utf-8") as f:
                f.write(threads_post)
            with open(lineoa_path, "w", encoding="utf-8") as f:
                f.write(lineoa_post)

            st.success("✅ 三份素材已依照 Step 1 格式生成完畢！")

            # ── 展示結果 ─────────────────────────────────────────
            st.markdown("---")
            st.markdown("### 📦 最終輸出成果")

            r1, r2, r3 = st.columns(3)
            with r1:
                st.markdown('<span class="platform-badge badge-line">LINE Flex</span>', unsafe_allow_html=True)
                flex_str = json.dumps(flex_json, ensure_ascii=False, indent=2)
                st.code(flex_str[:800] + ("..." if len(flex_str)>800 else ""), language="json")
                st.download_button("⬇️ 下載 JSON", flex_str, file_name=f"flex_{vid_id}.json")

            with r2:
                st.markdown('<span class="platform-badge badge-threads">Threads</span>', unsafe_allow_html=True)
                st.caption(f"格式要求：{format_settings.get('threads','')}")
                st.text_area("內容", threads_post, height=350, label_visibility="collapsed")
                st.download_button("⬇️ 下載 Threads", threads_post, file_name=f"threads_{vid_id}.txt")

            with r3:
                st.markdown('<span class="platform-badge badge-lineoa">LINE OA</span>', unsafe_allow_html=True)
                st.caption(f"格式要求：{format_settings.get('line_oa','')}")
                st.text_area("內容", lineoa_post, height=350, label_visibility="collapsed")
                st.download_button("⬇️ 下載 LINE OA", lineoa_post, file_name=f"lineoa_{vid_id}.txt")

        except Exception as e:
            st.error(f"❌ 生成失敗：{e}")

# ── 已生成素材清單 ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📂 已生成的行銷素材")
try:
    from config import SOURCE_DIR
    asset_dir = os.path.join(os.path.dirname(SOURCE_DIR), "marketing_assets")
    if os.path.exists(asset_dir):
        asset_files = sorted(os.listdir(asset_dir))
        if asset_files:
            for fn in asset_files:
                fpath = os.path.join(asset_dir, fn)
                fsize = os.path.getsize(fpath)
                icon = "📄" if fn.endswith(".txt") else "📦"
                st.markdown(f"- {icon} `{fn}` — {fsize:,} bytes")
        else:
            st.info("尚無已生成的素材")
    else:
        st.info("素材資料夾尚未建立")
except Exception:
    pass
