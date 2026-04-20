import os
import numpy as np
import textwrap
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy import VideoClip, ImageClip, CompositeVideoClip, AudioFileClip
from matrix_stitcher import get_matrix_rows, stitch_matrix_phonetics

# --- 設定常數 ---
BG_PATH = "avatar.png"
AUDIO_PATH = "last.m4a"
SAFE_ZONE = [200, 150, 900, 630]
# 白板中心點
SZ_CENTER_X = (SAFE_ZONE[0] + SAFE_ZONE[2]) // 2
SZ_CENTER_Y = (SAFE_ZONE[1] + SAFE_ZONE[3]) // 2 - 100
OUTPUT_RES = (1080, 1920)
SPACING = 15
ROW_H = 145

def get_font(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except:
        return ImageFont.load_default()

def create_base_canvas(show_backboard=True):
    base = Image.open(BG_PATH).convert("RGBA")
    base = base.resize(OUTPUT_RES, Image.Resampling.LANCZOS)
    if show_backboard:
        overlay = Image.new("RGBA", OUTPUT_RES, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle(SAFE_ZONE, fill=(255, 255, 255, 60))
        return Image.alpha_composite(base, overlay)
    return base

def make_natural_feather_blur_bg(minum_str):
    """
    製作帶有羽化邊緣的局部模糊 (讓白板模糊更自然)
    """
    full_ph = stitch_matrix_phonetics(minum_str)
    canvas = create_base_canvas(show_backboard=False)
    canvas.paste(full_ph, (200, 150), full_ph)
    
    # 1. 製作全畫面模糊版本
    full_blurred = canvas.filter(ImageFilter.GaussianBlur(12)) # 稍微降低點
    
    # 2. 製作漸層遮罩 (Feathered Mask)
    mask = Image.new("L", OUTPUT_RES, 0)
    draw = ImageDraw.Draw(mask)
    # 在安全區畫一個白色矩形
    draw.rectangle(SAFE_ZONE, fill=255)
    # 羽化遮罩邊緣
    mask = mask.filter(ImageFilter.GaussianBlur(10))
    
    # 3. 結合清晰底圖與模糊圖
    return Image.composite(full_blurred, canvas, mask)

def make_text_clip(text, size, duration, start_t):
    base = create_base_canvas(show_backboard=True)
    draw = ImageDraw.Draw(base)
    font = get_font(size)
    lines = textwrap.wrap(text, width=25)
    y_off = 310
    if len(lines) == 1: y_off = 390
    for line in lines:
        draw.text((200, y_off), line, fill=(0, 0, 0, 255), font=font)
        y_off += size + 10
    return ImageClip(np.array(base)).with_duration(duration).with_start(start_t)

def make_phonetic_animation_clips(minum_str, timestamps):
    rows = get_matrix_rows(minum_str)
    full_ph = stitch_matrix_phonetics(minum_str)
    
    bg_clean_img = create_base_canvas(show_backboard=False)
    bg_clean_img.paste(full_ph, (200, 150), full_ph)
    
    # 使用新版的「羽化漸層模糊」
    bg_blur_img = make_natural_feather_blur_bg(minum_str)
    
    ph_clips = []
    ph_clips.append(ImageClip(np.array(bg_clean_img)).with_start(timestamps[0]).with_duration(timestamps[1]-timestamps[0]))
    
    for i, row in enumerate(rows):
        if row is None: continue
        t_start = timestamps[i+1]
        t_end = timestamps[i+2]
        dur = t_end - t_start
        
        bg_clip = ImageClip(np.array(bg_blur_img)).with_start(t_start).with_duration(dur)
        
        orig_y = 150 + i * (ROW_H + SPACING)
        # 固定起點 X:200
        orig_x = 200 
        
        # 修正物件捕捉問題 (r=row)
        def make_frame_hq(t, r=row):
            p = min(t / 0.3, 1.0)
            scale = 1.0 + 0.5 * p
            w, h = r.size
            new_size = (int(w * scale), int(h * scale))
            return np.array(r.resize(new_size, Image.Resampling.LANCZOS))

        def make_pos(t, r=row):
            p = min(t / 0.3, 1.0)
            scale = 1.0 + 0.5 * p
            # 計算縮放後的寬度
            current_w = int(r.width * scale)
            # 水平中心對齊
            target_x = SZ_CENTER_X - (current_w // 2)
            # 垂直位移
            cur_x = orig_x + (target_x - orig_x) * p
            cur_y = orig_y + (SZ_CENTER_Y - orig_y) * p
            return (cur_x, cur_y)

        animated_row = VideoClip(make_frame_hq, duration=dur).with_start(t_start).with_position(make_pos)
        ph_clips.extend([bg_clip, animated_row])
        
    return ph_clips

def generate_final_v2_3():
    ts = [i * 6 for i in range(10)] # 縮短一點時間方便測試
    clips = []
    minum = '[[[1],[59,60]],[[15],[44]],[[4],[43]]]'
    clips.extend(make_phonetic_animation_clips(minum, ts[0:5]))
    
    final = CompositeVideoClip(clips, size=OUTPUT_RES)
    final.write_videofile("focus_v2_3_final.mp4", fps=24, logger=None)

if __name__ == "__main__":
    generate_final_v2_3()
