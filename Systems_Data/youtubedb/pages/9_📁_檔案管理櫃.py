import streamlit as st
import os
import glob
import math
import zipfile
import io
from core.config import SOURCE_DIR

st.set_page_config(page_title="檔案管理櫃", page_icon="📁", layout="wide")

st.title("📁 檔案管理櫃")
st.markdown("在這裡統一管理雲端主機上產出的所有實體檔案。您可以個別下載、批次打包，或是清理不再需要的媒體檔以節省空間。")

# 確保資料夾存在
if not os.path.exists(SOURCE_DIR):
    os.makedirs(SOURCE_DIR)

def get_file_size(filepath):
    size_bytes = os.path.getsize(filepath)
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def create_zip_of_files(file_paths):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for fpath in file_paths:
            if os.path.exists(fpath):
                zip_file.write(fpath, os.path.basename(fpath))
    return zip_buffer.getvalue()

# 分類取得檔案
all_files = glob.glob(os.path.join(SOURCE_DIR, "*.*"))
video_files = [f for f in all_files if f.endswith(".mp4") or f.endswith(".m4a")]
srt_files = [f for f in all_files if f.endswith(".srt")]
txt_files = [f for f in all_files if f.endswith(".txt")]

tab1, tab2, tab3 = st.tabs([f"✨ 策略文案區 ({len(txt_files)})", f"📝 逐字稿區 ({len(srt_files)})", f"🎬 影音原檔區 ({len(video_files)})"])

def render_file_manager(tab, files, file_type_name, empty_msg="目前沒有檔案"):
    with tab:
        if not files:
            st.info(empty_msg)
            return

        # 頂部工具列
        col_select, col_actions = st.columns([1, 2])
        
        # 狀態管理: 記錄被勾選的檔案
        if f"selected_{file_type_name}" not in st.session_state:
            st.session_state[f"selected_{file_type_name}"] = []

        # 全選按鈕邏輯
        with col_select:
            # 建立一個全選 checkbox
            select_all = st.checkbox("📋 全選本頁檔案", key=f"select_all_{file_type_name}")
            
        selected_files = []
        
        # 表格標頭
        c1, c2, c3, c4 = st.columns([1, 5, 2, 2])
        c1.markdown("**選取**")
        c2.markdown("**檔名**")
        c3.markdown("**大小**")
        c4.markdown("**個別下載**")
        st.markdown("---")
        
        # 顯示每個檔案
        for fpath in sorted(files, key=os.path.basename):
            fname = os.path.basename(fpath)
            c1, c2, c3, c4 = st.columns([1, 5, 2, 2])
            
            with c1:
                is_selected = st.checkbox(" ", key=f"chk_{fpath}", value=select_all)
                if is_selected:
                    selected_files.append(fpath)
            
            with c2:
                st.markdown(f"`{fname}`")
                
            with c3:
                st.caption(get_file_size(fpath))
                
            with c4:
                try:
                    with open(fpath, "rb") as f:
                        file_data = f.read()
                    
                    st.download_button(
                        label="📥 下載",
                        data=file_data,
                        file_name=fname,
                        key=f"dl_single_{fpath}"
                    )
                except Exception:
                    st.error("讀取失敗")
                    
        # 底部動作列 (批次下載 與 刪除)
        st.markdown("<br>", unsafe_allow_html=True)
        if selected_files:
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                # 批次下載 ZIP
                zip_data = create_zip_of_files(selected_files)
                st.download_button(
                    label=f"📦 打包下載選取的 {len(selected_files)} 個檔案 (.zip)",
                    data=zip_data,
                    file_name=f"batch_download_{file_type_name}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            
            with b_col2:
                # 批次刪除
                if st.button(f"🗑️ 永久刪除選取的 {len(selected_files)} 個檔案", key=f"del_{file_type_name}", use_container_width=True):
                    deleted_count = 0
                    for fpath in selected_files:
                        try:
                            os.remove(fpath)
                            deleted_count += 1
                        except:
                            pass
                    st.success(f"已刪除 {deleted_count} 個檔案。請重新整理頁面。")
                    st.rerun()

render_file_manager(tab1, txt_files, "txt", "尚無策略文案。去採收或精煉頁面生成吧！")
render_file_manager(tab2, srt_files, "srt", "尚無逐字稿。")
render_file_manager(tab3, video_files, "media", "尚無影音檔案。採收後會出現在這裡。")
