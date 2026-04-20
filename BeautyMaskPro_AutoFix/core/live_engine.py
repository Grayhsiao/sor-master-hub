import cv2
try:
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
except ImportError:
    from mediapipe.solutions import face_mesh as mp_face_mesh
import numpy as np
import time
import os

class RealTimeBeautyEngine:
    def __init__(self):
        self.mp_face_mesh = mp_face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.target_color_lab = None
        self.lightness_gain = 1.3
        self.tolerance = 35
        self.load_calibration()

    def load_calibration(self):
        """從設定檔讀取已校準的顏色"""
        try:
            if os.path.exists("config_color.txt"):
                with open("config_color.txt", "r") as f:
                    rgb = list(map(int, f.read().strip().split(",")))
                    pixel_np = np.uint8([[rgb]])
                    self.target_color_lab = cv2.cvtColor(pixel_np, cv2.COLOR_RGB2LAB)[0][0]
                    print(f"✅ 已載入校準顏色: {rgb}")
        except Exception as e:
            print(f"⚠️ 載入校準失敗: {e}")

    def set_config(self, gain, tolerance):
        self.lightness_gain = gain
        self.tolerance = tolerance

    def process_frame(self, frame):
        """
        處理每一影格：1. 定位臉部 2. 生成局部遮罩 3. 校色
        """
        # OpenCV 預設是 BGR，轉為 RGB 給 Mediapipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return frame # 沒偵測到臉，回傳原圖

        h, w, _ = frame.shape
        face_landmarks = results.multi_face_landmarks[0]
        
        # 1. 建立臉部區域 Mask (避免影響背景)
        face_points = np.array([
            [int(l.x * w), int(l.y * h)] 
            for l in face_landmarks.landmark
        ])
        face_hull = cv2.convexHull(face_points)
        face_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(face_mask, face_hull, 255)

        # 2. 局部校色邏輯
        lab_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2LAB).astype(np.float32)
        
        # 如果還沒校準顏色，先不做處理
        if self.target_color_lab is None:
            return frame

        # 計算當前影格與目標顏色的距離 (在 LAB 空間)
        # 這裡使用色彩差異 (Delta E) 的簡化版本
        dist_mask = np.sqrt(np.sum((lab_frame - self.target_color_lab)**2, axis=2))
        
        # 將距離轉換為 0-255 的遮罩
        # 距離越近 (小於 tolerance)，遮罩越白 (255)
        thresh_mask = np.where(dist_mask < self.tolerance, 255, 0).astype(np.uint8)
        
        # 結合臉部範圍
        final_mask = cv2.bitwise_and(thresh_mask, face_mask)
        
        # 羽化處理 (核心：確保邊緣自然)
        final_mask = cv2.GaussianBlur(final_mask, (41, 41), 0)

        # 3. 提亮處理
        l, a, b_chan = cv2.split(cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2LAB))
        l_float = l.astype(np.float32)
        mask_norm = final_mask.astype(np.float32) / 255.0
        
        # 提亮公式：只針對深色區域進行細微補償
        l_float = l_float * (1 + (self.lightness_gain - 1) * mask_norm)
        l_float = np.clip(l_float, 0, 255).astype(np.uint8)

        # 合併回 BGR
        res_lab = cv2.merge([l_float, a, b_chan])
        res_rgb = cv2.cvtColor(res_lab, cv2.COLOR_LAB2RGB)
        return cv2.cvtColor(res_rgb, cv2.COLOR_RGB2BGR)

    def calibrate_color(self, frame, x, y):
        """點擊選色校準"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pixel = rgb[y, x]
        # 轉換為 LAB 儲存
        pixel_np = np.uint8([[pixel]])
        self.target_color_lab = cv2.cvtColor(pixel_np, cv2.COLOR_RGB2LAB)[0][0]
        return pixel
