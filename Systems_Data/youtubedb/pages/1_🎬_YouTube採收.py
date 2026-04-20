import streamlit as st
import sys
import os
import threading
import time

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
    target_model = st.selectbox("AI 模型", [
        "gpt-5.4 (OpenAI 目前最強)", 
        "gpt-4o (OpenAI 原廠 直連)", 
        "gemini-3-flash (Google 原廠 直連)",
        "gemini-2.5-flash (Google 原廠 直連)",
        "claude-3-5-sonnet (OpenRouter 轉傳)"
    ], index=0)
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

            # ── 並行處理設定 ──
            MAX_DOWNLOAD_THREADS = 3

            # ── 進度 UI 佔位符 ──
            progress_overall = st.progress(0, text="準備中...")
            st.markdown("---")
            
            # 用於顯示多個下載任務的容器
            st.markdown("**📥 同時下載池 (最多 3 個)**")
            download_slots = [st.empty() for _ in range(MAX_DOWNLOAD_THREADS)]
            st.markdown("---")
            
            st.markdown("**🎙️ 目前轉錄與 AI 處理狀態**")
            transcription_status = st.empty()
            transcription_progress = st.progress(0)

            log_area = st.empty()
            logs = []

            def add_log(msg, icon=None):
                prefix = icon + " " if icon else ""
                logs.append(f"[{time.strftime('%H:%M:%S')}] {prefix}{msg}")
                log_area.code("\n".join(logs[-15:]), language="")

            import queue
            from concurrent.futures import ThreadPoolExecutor
            import threading

            # 下載完成後的佇列
            transcription_queue = queue.Queue()
            
            slot_lock = threading.Lock()
            free_slots = list(range(MAX_DOWNLOAD_THREADS))
            active_downloads = {} # thread_id -> slot_idx

            # ── 定義下載進度鉤子 (修正為支援多線程) ──
            def multi_download_hook(d):
                tid = threading.get_ident()
                slot_idx = None
                with slot_lock:
                    slot_idx = active_downloads.get(tid)
                
                if slot_idx is not None:
                    if d['status'] == 'downloading':
                        p_str = d.get('_percent_str', '0%')
                        speed = d.get('_speed_str', 'N/A')
                        title = d.get('info_dict', {}).get('title', '未知影片')
                        short_title = (title[:20] + '..') if len(title) > 20 else title
                        download_slots[slot_idx].markdown(f"⏳ **{short_title}**: {p_str} ({speed})")
                    elif d['status'] == 'finished':
                        download_slots[slot_idx].markdown("✅ 下載完成，等待轉錄...")

            def download_worker(v_url, v_id, v_title):
                tid = threading.get_ident()
                my_slot = None
                with slot_lock:
                    if free_slots:
                        my_slot = free_slots.pop(0)
                        active_downloads[tid] = my_slot
                
                try:
                    filepath, video_id, clean_title = download_video(v_url, progress_hooks=[multi_download_hook])
                    transcription_queue.put((filepath, video_id, clean_title))
                except Exception as e:
                    add_log(f"下載失敗 ({v_id}): {e}", "❌")
                    transcription_queue.put(None)
                finally:
                    if my_slot is not None:
                        with slot_lock:
                            free_slots.append(my_slot)
                            if tid in active_downloads:
                                del active_downloads[tid]
                            download_slots[my_slot].empty()

            # ── 解析網址列表 ──
            all_video_tasks = []
            for raw_url in urls:
                add_log(f"解析網址: {raw_url}", "🔍")
                info = get_video_info(raw_url)
                if info and "entries" in info:
                    for e in info["entries"]:
                        v_lnk = e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}"
                        all_video_tasks.append((v_lnk, e.get('id'), e.get('title')))
                elif info:
                    all_video_tasks.append((raw_url, info.get('id'), info.get('title')))

            total_tasks = len(all_video_tasks)
            if total_tasks == 0:
                st.warning("沒有找到可處理的影片。")
            else:
                # ── 開始啟動執行緒池下載 ──
                from streamlit.runtime.scriptrunner import add_script_run_ctx
                executor = ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_THREADS)
                for t_url, t_id, t_title in all_video_tasks:
                    future = executor.submit(download_worker, t_url, t_id, t_title)
                    # 這一行能消除 "missing ScriptRunContext" 警告
                    add_script_run_ctx(threading.enumerate()[-1])
                
                done_count = 0
                while done_count < total_tasks:
                    try:
                        result = transcription_queue.get(timeout=1)
                        if result:
                            fpath, vid, title = result
                            add_log(f"開始處理轉錄: {title}", "🎙️")
                            transcription_status.markdown(f"🎙️ **轉錄中**: {title}...")
                            transcription_progress.progress(0.2)
                            
                            srt_fn, trans_text = transcribe_video(fpath, vid, title, msg_callback=add_log)
                            if srt_fn:
                                update_index(vid, srt_fn)
                                transcription_progress.progress(0.6)
                                if generate_strategy and trans_text:
                                    transcription_status.markdown(f"🧠 **AI 文案精煉中 ({target_model})**: {title}...")
                                    strategy = generate_sor_content(title, trans_text, target_model)
                                    s_path = os.path.join(SOURCE_DIR, srt_fn.replace(".srt", "_strategy.txt"))
                                    with open(s_path, "w", encoding="utf-8") as f:
                                        f.write(strategy)
                                    add_log(f"策略文案已儲存: {title}", "📝")
                                    with st.expander(f"✨ 點我看 {title} 的 AI 策略文案", expanded=False):
                                        st.markdown(strategy)
                                        st.download_button(
                                            label="📥 點我下載此文案 (.txt)",
                                            data=strategy,
                                            file_name=srt_fn.replace(".srt", "_strategy.txt"),
                                            mime="text/plain",
                                            key=f"dl_{vid}"
                                        )
                                
                                transcription_progress.progress(1.0)
                                add_log(f"完成所有流程: {title}", "✅")
                            else:
                                add_log(f"轉錄失敗 (可能檔案太大或 API 錯誤): {title}", "❌")
                                transcription_status.markdown(f"❌ **轉錄失敗**: {title}")
                                transcription_progress.progress(0)
                        
                        done_count += 1
                        progress_overall.progress(done_count / total_tasks, text=f"總進度：{done_count}/{total_tasks}")
                    except queue.Empty:
                        pass
                
                executor.shutdown(wait=True)
                progress_overall.progress(1.0, text="🎉 所有採收任務已完成！")
                transcription_status.empty()
                transcription_progress.empty()
                st.success(f"✅ 成功處理 {done_count} 支影片，請前往「知識庫搜尋」頁面重建資料庫後，即可搜尋內容。")

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

    srt_files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.srt")), key=os.path.getmtime, reverse=True)
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
