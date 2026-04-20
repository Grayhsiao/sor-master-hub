import os
import re
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy import VideoClip, ImageClip, CompositeVideoClip, AudioFileClip, ColorClip
from matrix_stitcher import get_matrix_rows, stitch_matrix_phonetics, get_intonation_layer

# --- 【全域生產配置 V5.3 - 嚴格遵守 V4.6.3 座標合約】 ---
RES = (1080, 1920)
FPS = 30
OUTPUT_DIR = "output_videos"
BG_PATH = "avatar.png"
SHOW_GUIDES = True  

# 🎯 V4.6.3 座標合約 - 不可變動
X_START, X_END = 200, 900
Y_TOP, Y_BOTTOM = 125, 630
# 音標矩陣從 Y=150 開始 (draw_layout_wireframe.py 第 22 行)
PH_Y = 150
# Row 步進 = 160px (draw_layout_wireframe.py 第 44 行: 150 + i*160)
ROW_STEP = 160
# 藍框幾何中心
B_CENTER = (550, (Y_TOP + Y_BOTTOM) // 2)  # (550, 377)

COLOR_BLACK = (0, 0, 0, 255)
COLOR_VOWEL = (230, 57, 70, 255)
COLOR_BOARD_BLUE = (0, 0, 255, 255)
COLOR_ROW_GREY = (120, 120, 120, 255)

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

# --- 【核心工具函數】 ---

def get_vowel_segments(word):
    pattern = re.compile(r'([aeiouAEIOU]+)|([^aeiouAEIOU]+)')
    segments = []
    for m in pattern.finditer(word):
        text = m.group(0)
        is_vowel = bool(m.group(1))
        segments.append((text, is_vowel))
    return segments

def draw_vowel_text(draw, pos, segments, font, anchor='lm'):
    curr_x, curr_y = pos
    total_w = sum([draw.textlength(t, font=font) for t, _ in segments])
    if anchor == 'mm': curr_x -= total_w // 2
    for text, is_vowel in segments:
        color = COLOR_VOWEL if is_vowel else COLOR_BLACK
        draw.text((curr_x, curr_y), text, fill=color, font=font, anchor='lm')
        curr_x += draw.textlength(text, font=font)

def draw_wrapped_text(draw, pos, text, font, max_w=700, line_h=80):
    """
    自動換行：支援最多 3 行，垂直居中於 pos
    """
    words = text.split(' ')
    lines = []
    curr_line = ""
    for w in words:
        test_line = curr_line + (" " if curr_line else "") + w
        if draw.textlength(test_line, font=font) <= max_w:
            curr_line = test_line
        else:
            if curr_line: lines.append(curr_line)
            curr_line = w
    if curr_line: lines.append(curr_line)
    
    lines = lines[:3] 
    total_h = len(lines) * line_h
    start_y = pos[1] - (total_h // 2)
    for i, line in enumerate(lines):
        ly = start_y + i * line_h + (line_h // 2)
        draw.text((pos[0], ly), line, fill=COLOR_BLACK, font=font, anchor='mm')

def get_base_canvas(with_guides=SHOW_GUIDES):
    canvas = Image.open(BG_PATH).convert("RGBA").resize(RES)
    if with_guides:
        draw = ImageDraw.Draw(canvas)
        # 藍色主框 (V4.6.3)
        draw.rectangle([X_START, Y_TOP, X_END, Y_BOTTOM], outline=COLOR_BOARD_BLUE, width=6)
        # 灰色 Row 框 - 依照 wireframe: Y = 150 + i*160, 高 145
        for i in range(3):
            ry = PH_Y + i * ROW_STEP
            draw.rectangle([X_START, ry, X_END, ry + 145], outline=COLOR_ROW_GREY, width=4)
    return canvas

def make_blurred_bg(canvas, blur_radius=6):
    full_blurred = canvas.filter(ImageFilter.GaussianBlur(blur_radius))
    mask = Image.new("L", RES, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([X_START+10, Y_TOP+10, X_END-10, Y_BOTTOM-10], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(30))
    return Image.composite(full_blurred, canvas, mask)

# --- 【主渲染引擎】 ---

def render_word_video(row_data):
    word = str(row_data['單字'])
    minum = str(row_data['音標組合'])
    intonation = str(row_data.get('語調', ''))
    audio_file = str(row_data.get('音檔路徑', 'last.m4a'))
    
    # 讀取拍手對位的時間軸 T_* variables, 提供兼容 fallback 確保無拍手檔仍可運行
    t_matrix = pd.to_numeric(row_data.get('T_Matrix'), errors='coerce')
    if pd.isna(t_matrix): t_matrix = float(row_data.get('第一排', 1.5))

    t_row1 = pd.to_numeric(row_data.get('T_Row1'), errors='coerce')
    t_row2 = pd.to_numeric(row_data.get('T_Row2'), errors='coerce')
    t_row3 = pd.to_numeric(row_data.get('T_Row3'), errors='coerce')
    
    t_sent1 = pd.to_numeric(row_data.get('T_Sent1'), errors='coerce')
    t_img1 = pd.to_numeric(row_data.get('T_Img1'), errors='coerce')
    t_sent2 = pd.to_numeric(row_data.get('T_Sent2'), errors='coerce')
    t_img2 = pd.to_numeric(row_data.get('T_Img2'), errors='coerce')
    
    if not os.path.exists(audio_file): return
    audio = AudioFileClip(audio_file)
    dur = audio.duration

    try:
        font_main = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 145)
        font_sub = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 70)
    except:
        font_main = ImageFont.load_default(); font_sub = ImageFont.load_default()

    word_segs = get_vowel_segments(word)
    row_images_no_into = get_matrix_rows(minum, intonation_str=intonation, max_w=700, row_h=145, include_intonation=False)
    full_matrix = stitch_matrix_phonetics(minum, intonation_str=intonation, max_w=700, row_h=145)
    
    bg_clean = get_base_canvas()
    
    # 產生並貼上獨立的語調圖層 (增大為 40px, 原為 25px)
    intonation_img = get_intonation_layer(minum, intonation, max_w=700, row_h=145, target_height=40)
    if intonation_img:
        # 稍微向上移一點 (115)，讓放大的圖標更顯眼
        bg_clean.paste(intonation_img, (X_START, 115), intonation_img)
        
    bg_with_matrix = bg_clean.copy()
    bg_with_matrix.paste(full_matrix, (X_START, PH_Y), full_matrix)
    bg_blurred = make_blurred_bg(bg_with_matrix, blur_radius=6)
    clips = []

    # --- 【動態時間軸組合】 ---
    events = [
        ('S1', 0.0), 
        ('Matrix', t_matrix),
        ('R0', t_row1), 
        ('R1', t_row2),
        ('R2', t_row3),
        ('Sent1', t_sent1),
        ('Img1', t_img1),
        ('Sent2', t_sent2),
        ('Img2', t_img2),
        ('End', dur)
    ]
    
    valid_events = []
    for name, t in events:
        if pd.notna(t) and t <= dur: # 過濾掉超過總長度的意外點
            valid_events.append((name, float(t)))
            
    # 確保最終一定要以 dur 結束
    if valid_events[-1][0] != 'End':
        valid_events.append(('End', dur))

    for i in range(len(valid_events) - 1):
        name, start_t = valid_events[i]
        next_name, end_t = valid_events[i+1]
        c_dur = end_t - start_t
        if c_dur <= 0: continue
        
        if name == 'S1':
            def make_s1(t):
                img = bg_clean.copy()
                draw = ImageDraw.Draw(img)
                draw_vowel_text(draw, B_CENTER, word_segs, font_main, anchor='mm')
                return np.array(img)
            clips.append(VideoClip(make_s1, duration=c_dur).with_start(start_t))
            
        elif name == 'Matrix':
            def make_s2_factory(fade_dur):
                def make_s2(t):
                    img = bg_clean.copy()
                    p = min(t / max(fade_dur, 0.1), 1.0)
                    ph = full_matrix.copy()
                    alpha = int(255 * p)
                    orig_alpha = ph.split()[3]
                    faded_alpha = orig_alpha.point(lambda v: int(v * alpha / 255))
                    img.paste(ph, (X_START, PH_Y), faded_alpha)
                    return np.array(img)
                return make_s2
            # 將 fade in 設定為 0.4 秒或區間的一半
            fade_time = min(c_dur / 2, 0.4)
            clips.append(VideoClip(make_s2_factory(fade_time), duration=c_dur).with_start(start_t))
            
        elif name.startswith('R'):
            def make_focus_factory(r_img_param, orig_y_param):
                def make_focus(t):
                    p = min(t / 0.4, 1.0)
                    scale = 1.0 + 0.3 * p
                    rsz = r_img_param.resize((int(r_img_param.width*scale), int(r_img_param.height*scale)), Image.Resampling.LANCZOS)
                    scaled_vco = int((100 + 145//2) * scale)
                    tx = B_CENTER[0] - rsz.width // 2
                    ty = B_CENTER[1] - scaled_vco
                    cx = int(X_START + (tx - X_START) * p)
                    cy = int(orig_y_param + (ty - orig_y_param) * p)
                    f = bg_blurred.copy()
                    f.paste(rsz, (cx, cy), rsz)
                    return np.array(f)
                return make_focus
            
            r_idx = int(name[1])
            if r_idx < len(row_images_no_into) and row_images_no_into[r_idx]:
                r_img = row_images_no_into[r_idx]
                # S2_padding = 15, ZOOM_padding = 100
                oy = PH_Y + r_idx * 160 + 15 - 100
                clip_func = make_focus_factory(r_img, oy)
                clips.append(VideoClip(clip_func, duration=c_dur).with_start(start_t))
                
        elif name.startswith('Sent'):
            key = '例句１' if name == 'Sent1' else '例句２'
            val = str(row_data.get(key, ''))
            if val and val != 'nan':
                def make_txt_factory(txt):
                    def make_txt(t):
                        img = bg_clean.copy()
                        draw = ImageDraw.Draw(img)
                        draw_wrapped_text(draw, B_CENTER, txt, font_sub, max_w=700)
                        return np.array(img)
                    return make_txt
                clips.append(VideoClip(make_txt_factory(val), duration=c_dur).with_start(start_t))
                
        elif name.startswith('Img'):
            key = '圖片１' if name == 'Img1' else '圖片２'
            val = str(row_data.get(key, ''))
            if os.path.exists(val) and val != 'nan':
                r_img = Image.open(val).convert('RGBA').resize((600, 400))
                ix = B_CENTER[0] - r_img.width // 2
                iy = B_CENTER[1] - r_img.height // 2
                si = bg_clean.copy()
                si.paste(r_img, (ix, iy), r_img)
                clips.append(ImageClip(np.array(si)).with_start(start_t).with_duration(c_dur))
            
    from moviepy.audio.AudioClip import CompositeAudioClip
    final_video = CompositeVideoClip(clips, size=RES)
    final_video = final_video.with_audio(audio).with_duration(dur)
    
    out = f"{OUTPUT_DIR}/{word}_V5.3.mp4"
    final_video.write_videofile(out, fps=FPS, codec="libx264")
    print(f"✅ V5.3 完成: {out}")

def batch_process(csv_path):
    df = pd.read_csv(csv_path)
    for index, row in df.iterrows():
        try: render_word_video(row)
        except Exception as e: print(f"❌ 渲染失敗 [{row.get('單字')}]: {e}")

if __name__ == "__main__":
    if os.path.exists("production_test.csv"): batch_process("production_test.csv")
