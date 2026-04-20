import streamlit as st
import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="Facebook 採收 · 蕭博士 SoR", page_icon="📱", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0a3d2e 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(0,195,122,0.2);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }
section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)

# ── 標題 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>📱 Facebook 採收</h1>
    <p>啟動自動化爬蟲，偵測網頁內容並自動存檔。採收後內容將存於 fb_final_posts.txt</p>
</div>
""", unsafe_allow_html=True)

# ── 設定 ──────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    target_id = st.text_input("FB 目標 ID (或名稱)", value="1040899738", help="例如粉絲專頁的 ID 或自定義名稱")
with col2:
    min_length = st.number_input("最小存檔字數", value=100, min_value=10)

st.info("💡 啟動後會開啟 Chrome 瀏覽器，請在該瀏覽器手動登入 FB 後開始滑動頁面。")

# ── 執行邏輯 ──────────────────────────────────────────────────────────────────
if "fb_logs" not in st.session_state:
    st.session_state.fb_logs = []

if "scraping_active" not in st.session_state:
    st.session_state.scraping_active = False

log_area = st.empty()

def update_logs():
    log_area.code("\n".join(st.session_state.fb_logs[-30:]), language="")

def st_log(msg):
    st.session_state.fb_logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

if not st.session_state.scraping_active:
    if st.button("🚀 啟動 FB 採收器", type="primary", use_container_width=True):
        from import_fb_scraper import run_scraper
        st.session_state.scraping_active = True
        st.session_state.fb_logs = []
        st_log("準備啟動瀏覽器...")
        
        # 使用 Thread 避免阻塞 Streamlit
        def worker():
            run_scraper(target_id=target_id, min_length=min_length, log_func=st_log)
            st.session_state.scraping_active = False

        thread = threading.Thread(target=worker)
        thread.start()
        st.rerun()
else:
    st.warning("🔄 採收器執行中，請確認彈出的瀏覽器視窗。")
    if st.button("🛑 停止採收 (關閉瀏覽器)", use_container_width=True):
        # 這裡的停止邏輯依賴於 run_scraper 內部的 window 檢查
        st.session_state.scraping_active = False
        st_log("請直接手動關閉 Chrome 瀏覽器以停止。")
        st.rerun()

# 持續刷新 Log
if st.session_state.scraping_active:
    update_logs()
    time.sleep(1)
    st.rerun()
else:
    update_logs()

# ── 數據預覽 ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📄 採收數據概覽 (fb_final_posts.txt)")
if os.path.exists("fb_final_posts.txt"):
    with open("fb_final_posts.txt", "r", encoding="utf-8") as f:
        content = f.read()
    st.text_area("最新存檔內容", value=content[-2000:], height=300, help="僅顯示最後 2000 字")
else:
    st.info("尚無採收數據檔案。")
