import cv2
import numpy as np
from PIL import Image

class BeautyProcessor:
    def __init__(self):
        pass

    def apply_local_whitening(self, image_np, mask, lightness_gain=1.2):
        """
        針對遮罩區域進行局部提亮
        image_np: RGB 圖片 (numpy array)
        mask: 二值化遮罩 (與圖片同尺寸)
        lightness_gain: 亮度增益係數
        """
        # 轉換到 LAB 色彩空間
        lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)

        # 建立浮點數版本以避免溢位
        l_float = l.astype(np.float32)

        # 僅在遮罩區域進行提亮
        # 我們使用羽化的遮罩來進行平滑融合
        mask_normalized = mask.astype(np.float32) / 255.0
        
        # 提亮邏輯：L' = L * (1 + (gain-1) * mask)
        l_float = l_float * (1 + (lightness_gain - 1) * mask_normalized)
        
        # 確保數值在 0-255 之間
        l_float = np.clip(l_float, 0, 255).astype(np.uint8)

        # 合併回 LAB 並轉回 RGB
        balanced_lab = cv2.merge([l_float, a, b])
        result_rgb = cv2.cvtColor(balanced_lab, cv2.COLOR_LAB2RGB)
        
        return result_rgb

    def color_based_mask(self, image_np, target_color, tolerance=30):
        """
        基於顏色相似度生成遮罩
        target_color: (R, G, B)
        tolerance: 容差範圍
        """
        # 轉換為 HSV 進行更好的顏色對比
        hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
        
        target_np = np.uint8([[list(target_color)]])
        target_hsv = cv2.cvtColor(target_np, cv2.COLOR_RGB2HSV)[0][0]
        
        lower = np.array([max(0, target_hsv[0] - tolerance), 
                          max(0, target_hsv[1] - tolerance * 2), 
                          max(0, target_hsv[2] - tolerance * 2)])
        upper = np.array([min(180, target_hsv[0] + tolerance), 
                          min(255, target_hsv[1] + tolerance * 2), 
                          min(255, target_hsv[2] + tolerance * 2)])
        
        mask = cv2.inRange(hsv, lower, upper)
        
        # 使用形態學處理來消除噪點
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 羽化邊緣
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        return mask
