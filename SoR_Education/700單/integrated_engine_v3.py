import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from moviepy import VideoClip, ImageClip, CompositeVideoClip
from matrix_stitcher import get_matrix_rows, stitch_matrix_phonetics

# --- 【基本設定】 ---
OUTPUT_RES = (1080, 1920)
FPS = 30

# --- 【V3.8 旗艦精修版：銳利角色 + 座標微調】 ---
BG_PATH = "avatar.png"
# 座標下調至 90，達到視覺平衡
BOARD_POS = (65, 90)  
BOARD_SIZE = (950, 600)

CONTENT_W = 600
ROW_H = 145
SPACING = 15
TOTAL_PH_H = 3 * ROW_H + 2 * SPACING
PADDING_X = (BOARD_SIZE[0] - CONTENT_W) // 2
PADDING_Y = (BOARD_SIZE[1] - TOTAL_PH_H) // 2

B_CENTER_X = BOARD_SIZE[0] // 2
B_CENTER_Y = BOARD_SIZE[1] // 2

def make_localized_safe_blur_bg(content_img):
    """
    製作局部模糊背景：只模糊文字區，保護角色與框架的透明度
    """
    canvas = Image.open(BG_PATH).convert("RGBA").resize(OUTPUT_RES)
    
    # 產出全模糊底層
    full_blurred = canvas.filter(ImageFilter.GaussianBlur(15))
    
    # 製作「內縮遮罩」，保證模糊完全限制在黑板內部，且絕對不噴到人物身上
    mask = Image.new("L", OUTPUT_RES, 0)
    draw = ImageDraw.Draw(mask)
    # 遮罩範圍：根據 BOARD_POS 內縮 40px，且下方留更多 buffer 保護人物
    inset = 40
    draw.rectangle([BOARD_POS[0]+inset, BOARD_POS[1]+inset, 
                    BOARD_POS[0]+BOARD_SIZE[0]-inset, BOARD_POS[1]+BOARD_SIZE[1]-inset], fill=255)
    # 羽化遮罩邊緣，讓模糊與清晰背景自然融合
    mask = mask.filter(ImageFilter.GaussianBlur(25))
    
    # 複合：在原圖上只顯示「局部模糊區」
    canvas_final = Image.open(BG_PATH).convert("RGBA").resize(OUTPUT_RES)
    return Image.composite(full_blurred, canvas_final, mask)

def make_modular_phonetic_clips(min_um_str, timestamps):
    rows = get_matrix_rows(min_um_str)
    full_ph = stitch_matrix_phonetics(min_um_str, max_w=CONTENT_W)
    
    # 0. 底層乾淨背景
    bg_clean = Image.open(BG_PATH).convert("RGBA").resize(OUTPUT_RES)
    ph_layer = Image.new("RGBA", BOARD_SIZE, (0,0,0,0))
    ph_layer.paste(full_ph, (PADDING_X, PADDING_Y), full_ph)
    bg_clean.paste(ph_layer, BOARD_POS, ph_layer)
    
    # 1. 局部模糊景深背景 (保護角色人物)
    bg_blur_img = make_localized_safe_blur_bg(full_ph)
    
    clips = []
    # 全景
    clips.append(ImageClip(np.array(bg_clean)).with_start(timestamps[0]).with_duration(timestamps[1]-timestamps[0]))
    
    # 動效
    for i, row in enumerate(rows):
        if row is None: continue
        ts, te = timestamps[i+1], timestamps[i+2]
        dur = te - ts
        
        # 使用局部模糊底圖 (角色會是清晰的)
        bg_clip = ImageClip(np.array(bg_blur_img)).with_start(ts).with_duration(dur)
        
        orig_y = PADDING_Y + i * (ROW_H + SPACING)
        
        def make_frame_hq(t, r=row):
            p = min(t / 0.3, 1.0)
            scale = 1.0 + 0.3 * p
            img = r.resize((int(r.width * scale), int(r.height * scale)), Image.Resampling.LANCZOS)
            return np.array(img)

        def make_pos(t, r=row):
            p = min(t / 0.3, 1.0)
            scale = 1.0 + 0.3 * p
            w_scaled, h_scaled = int(r.width * scale), int(r.height * scale)
            target_x = B_CENTER_X - (w_scaled // 2)
            target_y = B_CENTER_Y - (h_scaled // 2)
            
            curr_x = BOARD_POS[0] + PADDING_X + (target_x - PADDING_X) * p
            curr_y = BOARD_POS[1] + orig_y + (target_y - orig_y) * p
            return (curr_x, curr_y)

        animated_row = VideoClip(make_frame_hq, duration=dur).with_start(ts).with_position(make_pos)
        clips.extend([bg_clip, animated_row])
        
    return clips

if __name__ == "__main__":
    min_um = "[70, 6, 45, 1, 40, 5, 59, 60, 20, 1]"
    times = [0, 2, 4, 6, 8, 10]
    
    clips = make_modular_phonetic_clips(min_um, times)
    final_video = CompositeVideoClip(clips, size=OUTPUT_RES)
    final_video.write_videofile("modular_demo_v3_1_green.mp4", fps=FPS, codec="libx264")
