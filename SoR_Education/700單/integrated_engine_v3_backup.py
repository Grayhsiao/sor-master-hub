import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from moviepy import VideoClip, ImageClip, CompositeVideoClip
from matrix_stitcher import get_matrix_rows, stitch_matrix_phonetics

# --- 【基本設定】 ---
OUTPUT_RES = (1080, 1920)
FPS = 30

# --- 【V3 旗艦模組設定 (寬屏優化版)】 ---
BG_PATH = "avatar.png"
SKIN_PATH = "board_skin_green.png"
BOARD_SIZE = (950, 600) # 加大尺寸
BOARD_POS = (65, 150)   # 向上提升 50 像素，避免擋到人物頭髮

# 內容安全區域
CONTENT_W = 600         # 限制基礎寬度，為了讓 1.5x 放大後 (900px) 仍能裝進 950px 的盒子
ROW_H = 145
SPACING = 15
TOTAL_PH_H = 3 * ROW_H + 2 * SPACING # 約 465px

# 計算內容在盒子內的起始偏移
PADDING_X = (BOARD_SIZE[0] - CONTENT_W) // 2
PADDING_Y = (BOARD_SIZE[1] - TOTAL_PH_H) // 2

B_CENTER_X = BOARD_SIZE[0] // 2
B_CENTER_Y = BOARD_SIZE[1] // 2

def create_board_canvas():
    """建立帶有 Skin 的盒子底圖"""
    if os.path.exists(SKIN_PATH):
        board = Image.open(SKIN_PATH).convert("RGBA")
        return board.resize(BOARD_SIZE, Image.Resampling.LANCZOS)
    return Image.new("RGBA", BOARD_SIZE, (255, 255, 255, 60))

def create_frame_only_canvas():
    """建立一個只有邊框、中間透明的遮罩 (匹配新 Skin 的 25px 邊框)"""
    skin = create_board_canvas()
    draw = ImageDraw.Draw(skin)
    # 挖空中間 (25px 是邊框厚度)
    draw.rectangle([25, 25, BOARD_SIZE[0]-25, BOARD_SIZE[1]-25], fill=(0,0,0,0))
    return skin

def make_natural_feather_board_bg(content_img):
    """
    製作帶有羽化邊緣的白板模糊背景
    """
    canvas = Image.open(BG_PATH).convert("RGBA").resize(OUTPUT_RES)
    board = create_board_canvas()
    # 內容貼在計算出的置中位置
    board.paste(content_img, (PADDING_X, PADDING_Y), content_img)
    
    full_blurred = canvas.copy()
    full_blurred.paste(board, BOARD_POS, board)
    full_blurred = full_blurred.filter(ImageFilter.GaussianBlur(15))
    
    mask = Image.new("L", OUTPUT_RES, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([BOARD_POS[0], BOARD_POS[1], BOARD_POS[0]+BOARD_SIZE[0], BOARD_POS[1]+BOARD_SIZE[1]], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(22)) # 羽化稍微加大
    
    canvas_final = Image.open(BG_PATH).convert("RGBA").resize(OUTPUT_RES)
    canvas_final.paste(board, BOARD_POS, board)
    return Image.composite(full_blurred, canvas_final, mask)

def make_modular_phonetic_clips(min_um_str, timestamps):
    rows = get_matrix_rows(min_um_str)
    # 以 CONTENT_W (600) 拼貼
    full_ph = stitch_matrix_phonetics(min_um_str, max_w=CONTENT_W, row_h=ROW_H, spacing=SPACING)
    
    # 展示清空畫布
    bg_clean = Image.open(BG_PATH).convert("RGBA").resize(OUTPUT_RES)
    board_clean = create_board_canvas()
    board_clean.paste(full_ph, (PADDING_X, PADDING_Y), full_ph)
    bg_clean.paste(board_clean, BOARD_POS, board_clean)
    
    bg_blur_img = make_natural_feather_board_bg(full_ph)
    frame_img = create_frame_only_canvas()
    
    clips = []
    # 0. 全景展示
    clips.append(ImageClip(np.array(bg_clean)).with_start(timestamps[0]).with_duration(timestamps[1]-timestamps[0]))
    
    # 1. 循環動效
    for i, row in enumerate(rows):
        if row is None: continue
        ts, te = timestamps[i+1], timestamps[i+2]
        dur = te - ts
        
        bg_clip = ImageClip(np.array(bg_blur_img)).with_start(ts).with_duration(dur)
        
        # 盒內相對 Y 起點
        orig_y = PADDING_Y + i * (ROW_H + SPACING)
        
        def make_frame_hq(t, r=row):
            p = min(t / 0.3, 1.0)
            scale = 1.0 + 0.5 * p
            img = r.resize((int(r.width * scale), int(r.height * scale)), Image.Resampling.LANCZOS)
            return np.array(img)

        def make_pos(t, r=row):
            p = min(t / 0.3, 1.0)
            scale = 1.0 + 0.5 * p
            w_scaled, h_scaled = int(r.width * scale), int(r.height * scale)
            target_x = B_CENTER_X - (w_scaled // 2)
            target_y = B_CENTER_Y - (h_scaled // 2)
            
            # 從原始 PADDING_X 位置 插值到 盒子中心
            curr_x = BOARD_POS[0] + PADDING_X + (target_x - PADDING_X) * p
            curr_y = BOARD_POS[1] + orig_y + (target_y - orig_y) * p
            return (curr_x, curr_y)

        animated_row = VideoClip(make_frame_hq, duration=dur).with_start(ts).with_position(make_pos)
        top_frame_clip = ImageClip(np.array(frame_img)).with_start(ts).with_duration(dur).with_position(BOARD_POS)
        
        clips.extend([bg_clip, animated_row, top_frame_clip])
        
    return clips

def generate_final_demo():
    print("🚀 正在啟動 V3.5 寬屏旗艦完稿渲染 (950x600 + 非破壞性縮放)...")
    min_um = "[70, 6, 45, 1, 40, 5, 59, 60, 20, 1]" # beautiful
    times = [0, 2, 4, 6, 8, 10]
    
    clips = make_modular_phonetic_clips(min_um, times)
    final_video = CompositeVideoClip(clips, size=OUTPUT_RES)
    final_video.write_videofile("modular_demo_v3_1_green.mp4", fps=FPS, codec="libx264")
    print("✨ 結案！寬屏旗艦版產出成功: modular_demo_v3_1_green.mp4")

if __name__ == "__main__":
    generate_final_demo()
