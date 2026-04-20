import streamlit as st
import cv2
import numpy as np
from PIL import Image
import sys
import os
import threading
import queue
import time

try:
    from core.live_engine import RealTimeBeautyEngine
except ImportError:
    # Fallback for local testing if core is not found or engine has import errors
    class RealTimeBeautyEngine:
        def set_config(self, *args): pass
        def process_frame(self, f): 
            # Simple dummy processing for fallback
            return cv2.putText(f.copy(), "Mock Processing", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        def load_calibration(self): pass

# Mock Video Capture for environments without a camera
class AutoMockCamera:
    def __init__(self):
        self.width, self.height = 640, 480
    def isOpened(self): return True
    def read(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Create a moving circle to simulate video
        t = time.time()
        x = int(self.width/2 + np.sin(t*2) * 100)
        y = int(self.height/2 + np.cos(t*2) * 100)
        cv2.circle(frame, (x, y), 50, (255, 100, 100), -1)
        cv2.putText(frame, "No Camera Detected", (50, self.height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Auto Mock Mode", (50, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        return True, frame
    def get(self, propId):
        if propId == cv2.CAP_PROP_FRAME_WIDTH: return self.width
        if propId == cv2.CAP_PROP_FRAME_HEIGHT: return self.height
        return 0
    def release(self): pass

# Optional Mock Camera for testing
if os.environ.get("MOCK_CAM") == "1":
    try:
        import mock_camera
    except ImportError:
        pass

class VirtualCamWrapper:
    def __init__(self, width, height, fps=30):
        try:
            import pyvirtualcam
            self.cam = pyvirtualcam.Camera(width=width, height=height, fps=fps)
            self.is_real = True
        except Exception:
            self.is_real = False
    
    def send(self, frame):
        if self.is_real:
            self.cam.send(frame)
    
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_real: self.cam.close()

st.set_page_config(page_title="Beauty Mask Pro | 即時會議版", page_icon="🎬", layout="wide")

st.title("🎬 Beauty Mask Pro: 會議室模式")
st.markdown("---")

@st.cache_resource
def get_engine():
    return RealTimeBeautyEngine()

engine = get_engine()
st.session_state.engine = engine

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ 即時控制面板")
    gain = st.slider("提亮強度", 1.0, 3.0, 1.3, step=0.1)
    tol = st.slider("顏色容差", 5, 100, 35)
    st.session_state.engine.set_config(gain, tol)
    
    st.markdown("---")
    start_cam = st.checkbox("🟢 啟動視訊處理", value=True)
    show_processed = st.checkbox("✨ 顯示校色後效果", value=True)
    
    st.markdown("---")
    if st.button("🎯 重新啟動校準"):
        st.info("請查看跳出的彈窗進行選色...")
        try:
            from calibrate import calibrate
            calibrate()
            st.session_state.engine.load_calibration()
            st.success("校準成功！")
        except Exception as e:
            st.error(f"校準發生錯誤: {e}")

    st.markdown("---")
    st.info("💡 **操作指南**：\n1. 點擊「🎯 重新啟動校準」並在跳出的視窗中點選胎記顏色。\n2. 按下 'q' 退出校準視窗。\n3. 勾選「🟢 啟動視訊處理」開始使用。")

col_video, col_settings = st.columns([3, 1])

with col_video:
    frame_placeholder = st.empty()

with col_settings:
    st.write("🔍 **系統狀態**")
    status_placeholder = st.empty()
    st.write("🎯 **當前模式**")
    mode_text = st.empty()

@st.fragment(run_every="0.05s")
def video_stream_fragment():
    if not st.session_state.get('start_cam', True):
        return

    status_placeholder.markdown("✅ **攝影機已連線 (串流中)**")
    mode_text.markdown("✨ **美顏校色中**" if show_processed else "📷 **原始畫面**")
    
    # Ensure camera is open
    if 'cap' not in st.session_state or st.session_state.cap is None:
        return
        
    ret, frame = st.session_state.cap.read()
    if not ret: 
        return
    
    frame = cv2.flip(frame, 1)
    processed = st.session_state.engine.process_frame(frame)
    display_frame = processed if show_processed else frame
    
    # Virtual camera output
    if 'vcam' in st.session_state and st.session_state.vcam is not None:
        rgb_vcam = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        st.session_state.vcam.send(rgb_vcam)
    
    # Browser display
    frame_placeholder.image(display_frame, channels="BGR", use_container_width=True)

# Save start_cam to session state to prevent fragment runaway
st.session_state.start_cam = start_cam

if start_cam:
    # Initialize resources
    if 'cap' not in st.session_state or st.session_state.cap is None:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.warning("⚠️ 偵測不到實體攝影機，已自動切換為模擬畫面 (Auto Mock Mode)")
            st.session_state.cap = AutoMockCamera()
        else:
            st.session_state.cap = cap
    
    if 'vcam' not in st.session_state or st.session_state.vcam is None:
        width = int(st.session_state.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(st.session_state.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        st.session_state.vcam = VirtualCamWrapper(width, height)
    
    # Run the fragment (it will auto-rerun every 0.05s)
    video_stream_fragment()
else:
    # 關閉並釋放資源
    if 'cap' in st.session_state and st.session_state.cap is not None:
        st.session_state.cap.release()
        st.session_state.cap = None
    if 'vcam' in st.session_state and st.session_state.vcam is not None:
        if st.session_state.vcam.is_real:
            st.session_state.vcam.cam.close()
        st.session_state.vcam = None
        
    st.info("👆 請勾選「啟動視訊處理」開始你的專屬美顏視訊之旅")
