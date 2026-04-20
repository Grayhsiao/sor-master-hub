import streamlit as st
import sys
import os
import glob
import subprocess
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="本地影片處理 · 蕭博士 SoR", page_icon="📁", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(139,92,246,0.25);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }
.video-card {
    background: rgba(22,27,34,0.9); border: 1px solid rgba(48,54,61,0.8);
    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    display: flex; justify-content: space-between; align-items: center;
}
.video-name { color: #E6EDF3; font-size: 0.9rem; font-weight: 500; }
.video-status { font-size: 0.75rem; color: rgba(230,237,243,0.5); }
section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)

# ── 標題 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>📁 本地影片處理</h1>
    <p>直接處理外接硬碟或本機資料夾中的影片檔。一鍵啟動：提取音訊 → Whisper 轉錄 → SoR 策略生成。</p>
</div>
""", unsafe_allow_html=True)

# ── 路徑處理邏輯 ─────────────────────────────────────────────────────────────
if "current_path" not in st.session_state:
    st.session_state.current_path = os.path.expanduser("~")
if "path_input" not in st.session_state:
    st.session_state.path_input = st.session_state.current_path

def update_path(new_path):
    st.session_state.current_path = new_path
    st.session_state.path_input = new_path

# 同步輸入框變動到 current_path
def on_path_input_change():
    st.session_state.current_path = st.session_state.path_input

col_path, col_model = st.columns([3, 1])

with col_path:
    st.markdown("**📂 影片存放路徑**")
    
    # 快捷按鈕
    c_vol, c_home, c_up, _ = st.columns([1, 1, 1, 4])
    with c_vol:
        st.button("🔌 外接硬碟", on_click=update_path, args=("/Volumes",), use_container_width=True)
    with c_home:
        st.button("🏠 家目錄", on_click=update_path, args=(os.path.expanduser("~"),), use_container_width=True)
    with c_up:
        parent = os.path.dirname(st.session_state.current_path)
        st.button("⬆️ 回上一層", on_click=update_path, args=(parent,), 
                  use_container_width=True, disabled=(parent == st.session_state.current_path))

    # 路徑輸入框
    st.text_input(
        "輸入資料夾路徑", 
        key="path_input",
        on_change=on_path_input_change,
        label_visibility="collapsed"
    )

with col_model:
    st.markdown("**🤖 AI 模型**")
    # 預設使用 gpt-4o，這是為了解決 Gemini 頻繁 429 的問題
    # Define a mapping from display labels to actual model names
    model_options_map = {
        "gpt-5.4 (OpenAI 目前最強)": "gpt-5.4",
        "gpt-4o (OpenAI 原廠 直連)": "gpt-4o",
        "gemini-3-flash (Google 原廠 直連)": "gemini-3-flash",
        "gemini-2.5-flash (Google 原廠 直連)": "gemini-2.5-flash",
        "claude-3-5-sonnet (OpenRouter 轉傳)": "openrouter/anthropic/claude-3-5-sonnet"
    }
    
    # Get the list of display labels for the selectbox
    display_labels = list(model_options_map.keys())
    
    # Find the index of the default selection
    default_index = display_labels.index("gpt-4o (OpenAI 原廠 直連)") if "gpt-4o (OpenAI 原廠 直連)" in display_labels else 0

    selected_label = st.selectbox(
        "核心 AI 模型", 
        display_labels, 
        index=default_index, 
        label_visibility="collapsed"
    )
    # Map the selected display label back to the actual model name
    target_model = model_options_map[selected_label]

    # 跳過片頭設定
    with st.expander("✂️ 跳過片頭設定", expanded=False):
        c_skip1, c_skip2 = st.columns(2)
        with c_skip1:
            global_skip = st.number_input("全域跳過秒數 (預設)", min_value=0, value=0, help="所有影片都會套用的預設跳過時間。")
        with c_skip2:
            use_ai_skip = st.toggle("🤖 AI 智能自動偵測 (Gemini)", value=False, help="開啟後系統會先讓 AI 聽前 60 秒，自動抓出人聲開始的時間點。")

    # 遞迴搜尋設定
    recursive_search = st.checkbox("🔍 包含子資料夾 (遞迴搜尋)", value=False, help="勾選後會連同所有子目錄中的影片一併找出。")

# ── 檔案瀏覽器 ──────────────────────────────────────────────────────────────
st.markdown("---")
video_files = []
if os.path.isdir(st.session_state.current_path):
    try:
        items = os.listdir(st.session_state.current_path)
        # 資料夾
        folders = sorted([f for f in items if os.path.isdir(os.path.join(st.session_state.current_path, f)) and not f.startswith(".")])
        # 影片副檔名
        exts = ('.mp4', '.mov', '.m4v', '.mkv', '.avi', '.flv')
        
        if recursive_search:
            video_files = []
            for root, dirs, files in os.walk(st.session_state.current_path):
                for f in files:
                    if f.lower().endswith(exts) and not f.startswith("."):
                        # 儲存相對於 current_path 的路徑
                        rel_path = os.path.relpath(os.path.join(root, f), st.session_state.current_path)
                        video_files.append(rel_path)
            video_files.sort()
        else:
            video_files = sorted([f for f in items if f.lower().endswith(exts) and not f.startswith(".")])
        
        st.markdown(f"📍 目前位置：`{st.session_state.current_path}`")
        
        if folders:
            st.caption("📁 子資料夾 (點擊進入)")
            f_cols = st.columns(4)
            for idx, f in enumerate(folders):
                with f_cols[idx % 4]:
                    new_p = os.path.join(st.session_state.current_path, f)
                    st.button(f"📁 {f}", key=f"folder_{idx}", on_click=update_path, args=(new_p,), use_container_width=True)
        
        if video_files:
            st.success(f"🎥 發現 {len(video_files)} 個影片檔案。")
            
            # 檔案搜尋過濾器
            search_query = st.text_input("🔍 搜尋影片檔名 (關鍵字)", "").strip().lower()
            if search_query:
                display_files = [f for f in video_files if search_query in f.lower()]
            else:
                display_files = video_files

            if not display_files:
                st.warning(f"🔍 找不到含「{search_query}」的影片。")
            
            # 檔案選取器
            selected_files = st.multiselect(
                "🎯 選取要處理的檔案 (預設全選)",
                options=display_files,
                default=display_files,
                help="你可以移除不想要處理的檔案，或手動挑選特定影片。"
            )
            
            if selected_files:
                # 最終處理清單使用選取的檔案
                video_files_to_process = selected_files 
                with st.expander(f"📝 待處理清單 ({len(selected_files)})", expanded=True):
                    # 建立一個 dict 來儲存個別覆蓋值
                    if "individual_skips" not in st.session_state:
                        st.session_state.individual_skips = {}
                    
                    st.write("您可以手動為特定影片設定不同的跳過秒數：")
                    for vf in selected_files:
                        c_name, c_sec = st.columns([3, 1])
                        with c_name:
                            st.markdown(f"🎬 {vf}")
                        with c_sec:
                            # 預設值帶入 global_skip
                            key = f"skip_{vf}"
                            val = st.number_input("跳過", min_value=0, value=global_skip, key=key, label_visibility="collapsed")
                            st.session_state.individual_skips[vf] = val
            else:
                st.warning("⚠️ 請至少選取一個檔案進行處理。")
                video_files_to_process = []
        else:
            st.info("ℹ️ 此資料夾內沒有可處理的影片。")
            video_files_to_process = []
            
    except Exception as e:
        st.error(f"❌ 無法讀取目錄: {e}")
else:
    st.error("❌ 無效的路徑或找不到該目錄。")

# ── 執行 ─────────────────────────────────────────────────────────────────────
if st.button("🚀 開始批次處理", type="primary", use_container_width=True, disabled=not video_files_to_process):
    try:
        # 強制重新讀取 .env，確保使用者更換 Key 後立即生效
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), "..", "core", ".env")
        load_dotenv(env_path, override=True)
        import utils, importlib
        importlib.reload(utils)
        
        # 重新初始化 API Client，確保核心邏輯使用新 Key
        import openai
        from google import genai
        import core.utils as utils
        
        o_key = os.getenv("OPENAI_API_KEY")
        g_key = os.getenv("GOOGLE_API_KEY")
        r_key = os.getenv("OPENROUTER_API_KEY")
        
        if o_key: utils.openai_client = openai.OpenAI(api_key=o_key)
        if g_key: utils.genai_client = genai.Client(api_key=g_key)
        if r_key:
            utils.openrouter_client = openai.OpenAI(
                api_key=r_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "SoR Video System"}
            )

        from core.config import SOURCE_DIR, DOWNLOAD_DIR
        import utils
        import importlib
        importlib.reload(utils)
        import time

        status_container = st.status("🔄 正在初始化系統...", expanded=True)
        logs = []

        def add_log(msg, icon=None):
            prefix = icon + " " if icon else ""
            logs.append(f"{prefix}{msg}")
            # 將最新三行顯示在 Status 標題
            status_container.update(label=f"🔄 處理中: {msg}", expanded=True)
            with status_container:
                st.write(f"{prefix}{msg}")

        # 診斷訊息：顯示 Key 的前 5 碼與後 4 碼，供使用者核對
        g_key_display = (g_key[:8] + "..." + g_key[-4:]) if g_key else "未設定"
        add_log(f"系統初始化... 讀取設定檔: {os.path.basename(env_path)}", icon="📂")
        add_log(f"目前使用的 Google Key: `{g_key_display}`", icon="🔑")

        progress_bar = st.progress(0, text="準備中...")
        
        for idx, filename in enumerate(video_files_to_process):
            video_path = os.path.join(st.session_state.current_path, filename)
            base_name = os.path.splitext(filename)[0]
            
            progress_val = idx / len(video_files_to_process)
            progress_bar.progress(progress_val, text=f"正在處理 ({idx+1}/{len(video_files_to_process)}): {filename}")
            status_container.update(label=f"🔄 正在處理: {filename} ({idx+1}/{len(video_files_to_process)})", state="running")
            
            add_log(f"🎬 開始處理: {filename}", icon="▶️")
            
            # 決定跳過秒數
            skip_secs = st.session_state.individual_skips.get(filename, global_skip)
            
            with st.spinner(f"正在為 {filename} 處理音訊..."):
                # 1. 提取音訊
                # 檔名加入 skip 資訊以利暫存區分
                audio_ext = "mp3"
                audio_name = f"{base_name}_ss{skip_secs}.{audio_ext}"
                audio_path = os.path.join(DOWNLOAD_DIR, audio_name)
                
                # 確保音訊存放目錄存在 (針對遞迴子目錄)
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                # 如果開啟 AI 偵測且目前的 skip_secs 還是預設值，則嘗試偵測
                if use_ai_skip and skip_secs == global_skip:
                    # 先提取一個臨時的完整(或前段)音訊供 AI 聽
                    temp_full_audio = os.path.join(DOWNLOAD_DIR, f"{base_name}_temp.mp3")
                    if not os.path.exists(temp_full_audio):
                        subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'libmp3lame', '-q:a', '9', '-y', temp_full_audio], capture_output=True)
                    
                    add_log("🤖 AI 模型分析中... 正在偵測人聲起點", icon="🧠")
                    ai_detected_skip = utils.detect_speech_start(temp_full_audio)
                    if ai_detected_skip > 0:
                        skip_secs = ai_detected_skip
                        add_log(f"🤖 AI 偵測成功：人聲從第 {skip_secs:.1f} 秒開始", icon="✨")
                        # 更新檔名
                        audio_name = f"{base_name}_ss{skip_secs:.1f}.{audio_ext}"
                        audio_path = os.path.join(DOWNLOAD_DIR, audio_name)
                    else:
                        add_log("🤖 AI 偵測結果：建議從頭開始轉錄", icon="ℹ️")
                
                if not os.path.exists(audio_path):
                    add_log(f"提取音訊中 (SS={skip_secs})...", icon="🎵")
                    cmd = ['ffmpeg', '-y']
                    if skip_secs > 0:
                        cmd.extend(['-ss', str(skip_secs)])
                    cmd.extend(['-i', video_path, '-vn', '-acodec', 'libmp3lame', '-q:a', '6', audio_path])
                    
                    subprocess.run(cmd, check=True, capture_output=True)
                    add_log("音訊提取完成", icon="✅")
                else:
                    add_log(f"音訊已存在 (SS={skip_secs})，跳過提取。", icon="ℹ️")
            
            with st.spinner(f"正在為 {filename} 進行 AI 轉譯..."):
                # 2. 轉錄
                srt_path = os.path.join(SOURCE_DIR, f"{base_name}.srt")
                os.makedirs(os.path.dirname(srt_path), exist_ok=True)
                
                if not os.path.exists(srt_path):
                    # 檢查是否需要特殊處理大檔案
                    file_size = os.path.getsize(audio_path)
                    if file_size > 24.5 * 1024 * 1024:
                        add_log(f"偵測到音訊較大 ({file_size/1024/1024:.1f}MB)，啟動自動分割轉譯流程...", icon="✂️")
                    else:
                        add_log("AI 轉譯中 (Whisper)...", icon="✍️")
                    
                    srt_content = utils.transcribe_audio_to_srt_large(audio_path, DOWNLOAD_DIR, SOURCE_DIR, base_name)
                    
                    if "Error" in srt_content:
                        add_log(f"轉譯失敗: {srt_content}", icon="❌")
                        continue
                    with open(srt_path, 'w', encoding='utf-8') as f:
                        f.write(srt_content)
                    add_log("逐字稿已儲存", icon="✅")
                else:
                    add_log("逐字稿已存在，跳過。", icon="ℹ️")
            
            with st.spinner(f"正在為 {filename} 生成 SoR 策略..."):
                # 3. 生成策略 - 統一命名規則：_strategy_{model_name}.txt
                strategy_path = os.path.join(SOURCE_DIR, f"{base_name}_strategy_{target_model}.txt")
                os.makedirs(os.path.dirname(strategy_path), exist_ok=True)
                
                if not os.path.exists(strategy_path):
                    add_log(f"生成 SoR 策略中 ({target_model})...", icon="🧠")
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                    transcript_clean = utils.clean_srt_to_text(srt_content)
                    strategy_content = utils.generate_sor_content(base_name, transcript_clean, model_name=target_model)
                    with open(strategy_path, 'w', encoding='utf-8') as f:
                        f.write(strategy_content)
                    add_log("策略文案已儲存", icon="✅")
                else:
                    add_log("策略文案已存在，跳過。", icon="ℹ️")
            
            progress_bar.progress((idx + 1) / len(video_files), text=f"已完成 {idx+1}/{len(video_files)}")

        status_container.update(label="🎉 批次處理完成！", state="complete", expanded=False)
        st.success("✅ 所有選取的影片已處理完畢！你現在可以前往「文案精煉」或「行銷素材」頁面查看成果。")

    except Exception as e:
        try:
            err_msg = str(e)
        except UnicodeEncodeError:
            err_msg = repr(e)
        st.error(f"❌ 執行中斷: {err_msg}")
        if 'status_container' in locals():
            status_container.update(label="❌ 執行出錯", state="error")
