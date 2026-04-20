import streamlit as st
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="YouTube 採收 · 蕭博士 SoR", page_icon="🎬", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0a2d1e 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(0,195,122,0.2);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }
.step-card {
    background: rgba(22,27,34,0.9); border: 1px solid rgba(48,54,61,0.8);
    border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1rem;
}
.step-number {
    display: inline-block; width: 28px; height: 28px; border-radius: 50%;
    background: #00C37A; color: #0D1117; text-align: center; line-height: 28px;
    font-weight: 700; font-size: 0.85rem; margin-right: 0.6rem;
}
section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)

# ── 側邊欄 ────────────────────────────────────────────────────────────────────

# ── 標題 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>🎬 YouTube 採收</h1>
    <p>貼入 YouTube 網址或播放清單，系統自動下載影片 → Whisper 轉錄逐字稿 → 生成 SoR 策略文案</p>
</div>
""", unsafe_allow_html=True)

# ── 輸入與設定 ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("**📎 輸入 YouTube 網址**")
    url_input = st.text_area(
        "網址（每行一個，或單一播放清單）",
        placeholder="https://www.youtube.com/watch?v=xxxxxx\nhttps://www.youtube.com/playlist?list=xxxxxx",
        height=120,
        label_visibility="collapsed"
    )

with col_right:
    st.markdown("**⚙️ 採收設定**")
    generate_strategy = st.toggle("自動生成 SoR 策略文案", value=True)
    target_model = st.selectbox("AI 模型", ["gpt-4o", "gemini"], index=0)
    st.caption("💡 生成策略文案會呼叫 AI API，會產生費用")

st.markdown("<br>", unsafe_allow_html=True)

# ── 工作流程說明 ──────────────────────────────────────────────────────────────
with st.expander("📋 了解採收流程", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("1", "解析 URL", "用 yt-dlp 取得影片資訊與清單"),
        ("2", "下載影片", "下載為 MP4，跳過已存在檔案"),
        ("3", "Whisper 轉錄", "呼叫 OpenAI Whisper 生成 .srt 字幕"),
        ("4", "策略生成", "GPT-4o 分析逐字稿，生成 SoR 策略文案"),
    ]
    for col, (num, title, desc) in zip([c1, c2, c3, c4], steps):
        with col:
            st.markdown(f"""
            <div class='step-card'>
                <span class='step-number'>{num}</span><strong>{title}</strong>
                <p style='color:rgba(230,237,243,0.5);font-size:0.82rem;margin:0.5rem 0 0;'>{desc}</p>
            </div>""", unsafe_allow_html=True)

# ── 執行 ─────────────────────────────────────────────────────────────────────
if st.button("🚀 開始採收", type="primary", use_container_width=True):
    urls = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
    if not urls:
        st.warning("⚠️ 請先輸入至少一個 YouTube 網址")
    else:
        try:
            from config import DOWNLOAD_DIR, SOURCE_DIR, INDEX_FILE
            from import_youtube_batch import get_video_info, download_video, transcribe_video, update_index
            from utils import generate_sor_content

            log_area = st.empty()
            logs = []

            def add_log(msg):
                logs.append(msg)
                log_area.code("\n".join(logs[-30:]), language="")

            progress = st.progress(0, text="準備中...")
            total_done = 0
            total_all = 0

            for raw_url in urls:
                add_log(f"\n🔍 解析：{raw_url}")
                info = get_video_info(raw_url)
                if info is None:
                    add_log("❌ 無法解析此 URL，跳過")
                    continue

                if "entries" in info:
                    entries = list(info["entries"])
                    add_log(f"📋 播放清單：找到 {len(entries)} 支影片")
                    total_all += len(entries)
                    video_urls = [
                        e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}"
                        for e in entries
                    ]
                else:
                    total_all += 1
                    video_urls = [raw_url]

                for v_url in video_urls:
                    add_log(f"\n⬇️ 下載中：{v_url}")
                    filepath, video_id, clean_title = download_video(v_url)
                    if not filepath:
                        add_log("❌ 下載失敗，跳過")
                        total_done += 1
                        continue

                    add_log(f"🎙️ 轉錄中：{clean_title}")
                    srt_filename, transcript_text = transcribe_video(filepath, video_id, clean_title)
                    if not srt_filename:
                        add_log("❌ 轉錄失敗")
                        total_done += 1
                        continue

                    update_index(video_id, srt_filename)
                    add_log(f"✅ 轉錄完成：{srt_filename}")

                    if generate_strategy and transcript_text:
                        add_log(f"✨ 生成 SoR 策略（{target_model}）...")
                        strategy = generate_sor_content(clean_title, transcript_text, target_model)
                        strategy_path = os.path.join(
                            SOURCE_DIR,
                            srt_filename.replace(".srt", "_strategy.txt")
                        )
                        with open(strategy_path, "w", encoding="utf-8") as f:
                            f.write(strategy)
                        add_log(f"📝 策略文案已儲存：{os.path.basename(strategy_path)}")

                    total_done += 1
                    if total_all > 0:
                        progress.progress(
                            total_done / total_all,
                            text=f"進度：{total_done}/{total_all}"
                        )

            progress.progress(1.0, text="🎉 採收完成！")
            st.success(f"✅ 共處理 {total_done} 支影片，請前往「知識庫搜尋」頁面重建資料庫後，即可搜尋內容。")

        except ImportError as e:
            st.error(f"❌ 模組載入失敗：{e}\n\n請確認 API Key 已設定（.env 檔案）")
        except Exception as e:
            st.error(f"❌ 執行失敗：{e}")

# ── 現有檔案清單 ──────────────────────────────────────────────────────────────
st.divider()
st.markdown("**📂 已採收的影片**")
try:
    from config import SOURCE_DIR
    import glob, json

    srt_files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.srt")))
    if srt_files:
        for sf in srt_files:
            base = os.path.basename(sf)
            has_strategy = os.path.exists(sf.replace(".srt", "_strategy.txt"))
            icon = "✅" if has_strategy else "⏳"
            st.markdown(f"- {icon} `{base}` {'（已有策略文案）' if has_strategy else '（待生成策略文案）'}")
    else:
        st.info("尚無採收的影片，請貼入網址後開始採收。")
except Exception:
    st.info("無法讀取資料夾狀態。")
