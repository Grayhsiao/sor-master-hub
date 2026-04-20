import streamlit as st
import sys
import os
import time
from pathlib import Path

# 確保可以 import core 內容
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from import_fb_scraper import FBScraper

st.set_page_config(page_title="FB 貼文採收", page_icon="📱", layout="wide")

st.title("📱 Facebook 貼文自動化採收")
st.markdown("""
本工具可自動爬取 FB 專頁貼文，並依關鍵字自動分流。
1. **第一次使用**：請先點擊「開啟瀏覽器登入」，手動登入後點擊「儲存 Cookie」。
2. **後續使用**：直接輸入 ID 並設定捲動次數，點擊「開始自動採收」即可。
""")

# 為了避免 Streamlit 快取舊版的 Class 定義導致 TypeError，我們在每次重整時檢查
if 'scraper' not in st.session_state:
    st.session_state.scraper = FBScraper()
else:
    # 檢查是否有新版的參數，若無則重新初始化
    import inspect
    sig = inspect.signature(st.session_state.scraper.scrape_posts)
    if 'clear_rejected' not in sig.parameters:
        st.session_state.scraper = FBScraper()

scraper = st.session_state.scraper

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ 設定")
    target_id = st.text_input("FB 專頁 ID (或唯一名稱)", value=scraper.target_id)
    scroll_limit = st.number_input("自動捲動次數 (每次約 3-5 篇)", min_value=1, max_value=100, value=10)
    
    st.divider()
    
    if st.button("🌐 1. 開啟瀏覽器 (手動模式/登入)", use_container_width=True):
        scraper.init_driver(headless=False)
        scraper.driver.get(f"https://www.facebook.com/{target_id}")
        st.info("瀏覽器已開啟。請在瀏覽器中完成登入或確認頁面，完畢後請點擊下方「儲存 Cookie」。")

    if st.button("💾 2. 儲存 Cookie (免重複登入)", use_container_width=True):
        if scraper.driver:
            scraper.save_cookies()
            st.success("Cookie 已儲存！下次採收將自動嘗試登入。")
        else:
            st.error("請先開啟瀏覽器。")

    st.divider()

    if st.button("🚀 3. 開始自動採收", type="primary", use_container_width=True):
        scraper.target_id = target_id
        
        status_area = st.empty()
        log_area = st.empty()
        
        progress_bar = st.progress(0)
        
        def update_status(msg):
            status_area.write(f"⏳ **狀態**: {msg}")

        # 嘗試載入 Cookie
        if not scraper.driver:
            scraper.init_driver(headless=False) # 暫時不用 headless 方便觀察
            has_cookies = scraper.load_cookies()
            if not has_cookies:
                st.warning("未偵測到 Cookie，將以訪客身分或需要手動登入。")
        else:
            has_cookies = True # 瀏覽器若已開著，就直接用目前的狀態
        
        with st.spinner("採收中...請勿關閉瀏覽器"):
            scraper.scrape_posts(scroll_limit=scroll_limit, status_callback=update_status, clear_rejected=True)
            status_area.write("✅ **狀態**: 採收程序已結束")
            progress_bar.progress(100)
            
        st.success(f"採收完成！\n✅ 新增精華: {scraper.valid_count} 篇\n🗑️ 隔離廢文: {scraper.rejected_count} 篇")
        
        if scraper.driver:
            # scraper.driver.quit()
            st.info("採收完畢，瀏覽器可手動關閉或保留。")

with col2:
    st.subheader("📊 採收成果預覽")
    
    output_path = Path(scraper.output_file)
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        st.text_area("精華區 (fb_final_posts.txt)", value=content, height=400)
    else:
        st.info("尚無採收資記錄。")

    rejected_path = Path(scraper.rejected_file)
    if rejected_path.exists():
        with st.expander("查看隔離區"):
            with open(rejected_path, "r", encoding="utf-8") as f:
                rej_content = f.read()
            st.text(rej_content)
