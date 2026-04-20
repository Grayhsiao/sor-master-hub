import os
import re
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy.editor import VideoClip, ImageClip, CompositeVideoClip, AudioFileClip, ColorClip
from matrix_stitcher import get_matrix_rows, stitch_matrix_phonetics

# --- 【全域生產配置 V5.3 - 嚴格遵守 V4.6.3 座標合約】 ---
RES = (1080, 1920)
FPS = 30
OUTPUT_DIR = "output_videos"
BG_PATH = "avatar.png"
SHOW_GUIDES = True  

# 🎯 V4.6.3 座標合約 - 不可變動
X_START, X_END = 200, 900
Y_TOP, Y_BOTTOM = 125, 630
# 音標矩陣從 Y=125 開始
PH_Y = 125
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
    if anchor in ['mm', 'ms']: 
        curr_x -= total_w // 2
        
    for text, is_vowel in segments:
        color = COLOR_VOWEL if is_vowel else COLOR_BLACK
        actual_anchor = 'ls' if anchor == 'ms' else ('lm' if anchor == 'mm' else anchor)
        draw.text((curr_x, curr_y), text, fill=color, font=font, anchor=actual_anchor)
        curr_x += draw.textlength(text, font=font)

def draw_wrapped_text(draw, text, font, max_w=700):
    """
    自動換行：支援最多 3 行，強制對齊三分格基準線
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
    
    # 網格底線 (Baseline) - 讓字體坐在這線上 (精確符合 Row 1: 150~295, 2: 310~455, 3: 470~615)
    baselines = [280, 440, 600]
    
    # 如果只有一行，強制放第二格 (中間)
    if len(lines) == 1:
        draw.text((B_CENTER[0], baselines[1]), lines[0], fill=COLOR_BLACK, font=font, anchor='ms')
    elif len(lines) == 2:
        draw.text((B_CENTER[0], baselines[0]), lines[0], fill=COLOR_BLACK, font=font, anchor='ms')
        draw.text((B_CENTER[0], baselines[1]), lines[1], fill=COLOR_BLACK, font=font, anchor='ms')
    else:
        for i, line in enumerate(lines):
            draw.text((B_CENTER[0], baselines[i]), line, fill=COLOR_BLACK, font=font, anchor='ms')

def get_base_canvas(with_guides=SHOW_GUIDES):
    # 恢復使用 avatar.png 作為背景
    try:
        canvas = Image.open(BG_PATH).convert("RGBA").resize(RES)
    except:
        canvas = Image.new("RGBA", RES, (255, 255, 250, 255))
        
    draw = ImageDraw.Draw(canvas)
    if with_guides:
        # 藍色主框
        draw.rectangle([X_START, Y_TOP, X_END, Y_BOTTOM], outline=COLOR_BOARD_BLUE, width=6)
        # 三等份內分割線 (位於間隙 15px 的中央: 302 與 462)
        draw.line([(X_START, 302), (X_END, 302)], fill=COLOR_BOARD_BLUE, width=3)
        draw.line([(X_START, 462), (X_END, 462)], fill=COLOR_BOARD_BLUE, width=3)
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
    # 動態產生排數與高度，把 intonation 傳進去
    row_images_with_into = get_matrix_rows(minum, intonation_str=intonation, max_w=700, target_h=145, top_padding=0)
    full_matrix = stitch_matrix_phonetics(minum, intonation_str=intonation, max_w=700, target_h=145)
    
    # --- 【AI 口型頭像整合】 ---
    # 檢查是否已有預生成的口型影片
    avatar_video_path = f"output_videos/avatar_temp/{word}_talking.mp4"
    use_video_bg = os.path.exists(avatar_video_path)
    
    bg_clean = get_base_canvas()
    
    if use_video_bg:
        print(f"🎬 使用 AI 口型背景: {avatar_video_path}")
        from moviepy.video.io.VideoFileClip import VideoFileClip
        # 強制為背景影片建立遮罩，使其成為 4 通道，以便與透明文字層合成
        bg_clip = VideoFileClip(avatar_video_path).set_duration(dur).resize(RES).add_mask()
    else:
        bg_clip = ImageClip(np.array(bg_clean)).set_duration(dur).add_mask()
        
    bg_with_matrix = bg_clean.copy()
    bg_with_matrix.paste(full_matrix, (X_START, PH_Y), full_matrix)
    bg_blurred = make_blurred_bg(bg_with_matrix, blur_radius=6)

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
        if pd.notna(t) and t <= dur: 
            valid_events.append((name, float(t)))
            
    if not valid_events or valid_events[-1][0] != 'End':
        valid_events.append(('End', dur))

    # --- 【一體化產線：Unified PIL Frame Generator】 ---
    def get_frame(t):
        # 1. 獲取底層 (影片影格或靜態圖片)
        if use_video_bg:
            canvas = Image.fromarray(bg_clip.get_frame(t)).convert("RGBA")
        else:
            canvas = bg_clean.copy()
            
        draw = ImageDraw.Draw(canvas)
        
        # 2. 判斷時間區間
        curr_name = "End"
        event_start = 0.0
        event_dur = dur
        for i in range(len(valid_events) - 1):
            if valid_events[i][1] <= t < valid_events[i+1][1]:
                curr_name = valid_events[i][0]
                event_start = valid_events[i][1]
                event_dur = valid_events[i+1][1] - valid_events[i][1]
                break
        
        rel_t = t - event_start
        
        # 3. 繪製對應層
        if curr_name == 'S1':
            draw_vowel_text(draw, (B_CENTER[0], 440), word_segs, font_main, anchor='ms')
            
        elif curr_name == 'Matrix':
            fade_in = min(event_dur / 2, 0.4)
            p = min(rel_t / max(fade_in, 0.1), 1.0)
            ph = full_matrix.copy()
            alpha = int(255 * p)
            if alpha < 255:
                r, g, b, a = ph.split()
                a = a.point(lambda v: int(v * alpha / 255))
                ph = Image.merge("RGBA", (r, g, b, a))
            canvas.paste(ph, (X_START, PH_Y), ph)
            
        elif curr_name.startswith('R'):
            r_idx = int(curr_name[1])
            if r_idx < len(row_images_with_into) and row_images_with_into[r_idx]:
                r_img = row_images_with_into[r_idx]
                grid_centers = [257, 417, 577]
                abs_cy = PH_Y + grid_centers[min(r_idx, 2)]
                canvas_b = make_blurred_bg(canvas, blur_radius=6)
                p = min(rel_t / 0.4, 1.0)
                scale = 1.0 + 0.3 * p
                rsz = r_img.resize((int(r_img.width*scale), int(r_img.height*scale)), Image.Resampling.LANCZOS)
                tx, ty = B_CENTER[0] - rsz.width // 2, B_CENTER[1] - rsz.height // 2
                orig_x, orig_y = X_START + (700 - r_img.width) // 2, abs_cy - r_img.height // 2
                canvas_b.paste(rsz, (int(orig_x + (tx - orig_x) * p), int(orig_y + (ty - orig_y) * p)), rsz)
                canvas = canvas_b
                
        elif curr_name.startswith('Sent'):
            key = '例句１' if curr_name == 'Sent1' else '例句２'
            val = str(row_data.get(key, ''))
            if val and val != 'nan':
                draw_wrapped_text(draw, val, font_sub, max_w=700)
                
        elif curr_name.startswith('Img'):
            key = '圖片１' if curr_name == 'Img1' else '圖片２'
            val = str(row_data.get(key, ''))
            if os.path.exists(val) and val != 'nan':
                r_img = Image.open(val).convert('RGBA').resize((600, 400))
                canvas.paste(r_img, (B_CENTER[0] - r_img.width // 2, B_CENTER[1] - r_img.height // 2), r_img)
        
        return np.array(canvas.convert("RGB"))

    final_video = VideoClip(get_frame, duration=dur)
    final_video = final_video.set_audio(audio)
    
    out_path = f"{OUTPUT_DIR}/{word}_V5.3.mp4"
    final_video.write_videofile(out_path, fps=FPS, codec="libx264")
    print(f"✅ V5.3 完成: {out_path}")
def batch_process(csv_path):
    df = pd.read_csv(csv_path)
    for index, row in df.iterrows():
        try: render_word_video(row)
        except Exception as e: print(f"❌ 渲染失敗 [{row.get('單字')}]: {e}")

if __name__ == "__main__":
    if os.path.exists("production_test.csv"): batch_process("production_test.csv")
