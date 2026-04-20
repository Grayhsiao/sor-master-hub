import os
import ast
from PIL import Image, ImageDraw, ImageFont
import textwrap
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
import pandas as pd

# ================= ⚙️ 設定區域 =================
AUDIO_FILE = "last.m4a"
BG_IMAGE = "avatar.png"
ASSETS_DIR = "drive-download-20260218T084106Z-1-001"
IMG_DIR = "圖庫"
OUTPUT_DIR = "phonetic_output"
FINAL_OUTPUT = "final_last_demo.mp4"

# 數據 (根據查找結果)
WORD_DATA = {
    'word': 'last',
    'minum': '[[[19],[49],[38,17]]]',
    'chinese': '最後的; 持續; 上回',
    'sent1': 'This is the last piece of cake.',
    'sent2': 'The movie lasts for two hours.',
    'img1': 'last去背.png',
    'img2': '7ff3db5a-018b-4604-814f-52df2db42f1a (1).png' # 使用另一張圖片作為 Demo 
}

# 視覺參數
OVERLAY_WIDTH = 500
SIDE_X, SIDE_Y = 150, 450
MAX_H = int(1920 * 0.4)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ================= 🛠 工具函式 =================

def get_best_font(size):
    paths = ["/System/Library/Fonts/PingFang.ttc", "/Library/Fonts/Arial Unicode.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_text_card(text, output_path, is_title=False):
    width, height = 500, 1000 
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_size = 100 if is_title else 70
    font = get_best_font(font_size)
    
    lines = textwrap.wrap(str(text), width=10 if is_title else 15)
    curr_y = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((width - w) // 2, curr_y), line, font=font, fill=(0,0,0,255))
        curr_y += font_size + 20
    
    img = img.crop((0, 0, width, curr_y + 20))
    img.save(output_path)
    return output_path

def stitch_phonetics_vertical(word, minum_str):
    try:
        data = ast.literal_eval(minum_str)
        symbols = data[0] if isinstance(data, list) and len(data) > 0 else []
        images = []
        for sym_list in symbols:
            for sym_id in sym_list:
                path = os.path.join(ASSETS_DIR, f"{sym_id}.png")
                if os.path.exists(path):
                    images.append(Image.open(path).convert("RGBA"))
        
        if not images: return None
        
        max_w = max(img.width for img in images)
        total_h = sum(img.height for img in images) + (len(images)-1)*20
        combined = Image.new("RGBA", (max_w, total_h), (0,0,0,0))
        curr_y = 0
        for img in images:
            x_off = (max_w - img.width) // 2
            combined.paste(img, (x_off, curr_y), img)
            curr_y += img.height + 20
        
        out_path = os.path.join(OUTPUT_DIR, f"{word}_demo_vert.png")
        combined.save(out_path)
        return out_path
    except: return None

# ================= 🎬 製作流程 =================

def make_demo():
    print("🚀 開始製作 1:52 Demo 影片...")
    audio = AudioFileClip(AUDIO_FILE)
    duration = audio.duration
    print(f"   ⏱ 音檔時長: {duration:.2f} 秒")

    # 分鏡順序與持續時間 (均分)
    # 順序: 單字 -> 音標 -> 字義 -> 圖片1 -> 例句1 -> 例句2 -> 圖片2
    scenes = ["word", "ph", "chinese", "img1", "sent1", "sent2", "img2"]
    num_scenes = len(scenes)
    scene_duration = duration / num_scenes
    
    # 1. 準備底圖
    base_clip = ImageClip(BG_IMAGE).with_duration(duration)
    # 確保底圖是 1080x1920
    base_clip = base_clip.resized(height=1920)
    if base_clip.w < 1080: base_clip = base_clip.resized(width=1080)
    base_clip = base_clip.cropped(x_center=base_clip.w/2, y_center=base_clip.h/2, width=1080, height=1920)
    base_clip = base_clip.with_audio(audio)

    overlay_clips = []
    temp_dir = "temp_demo"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)

    for i, scene in enumerate(scenes):
        start = i * scene_duration
        end = (i + 1) * scene_duration
        if i == num_scenes - 1: end = duration # 確保最後一個分鏡到結束
        
        img_path = None
        is_center = False
        
        if scene == "word":
            img_path = create_text_card(WORD_DATA['word'], os.path.join(temp_dir, "word.png"), is_title=True)
        elif scene == "ph":
            img_path = stitch_phonetics_vertical(WORD_DATA['word'], WORD_DATA['minum'])
        elif scene == "chinese":
            img_path = create_text_card(WORD_DATA['chinese'], os.path.join(temp_dir, "chinese.png"))
        elif scene == "img1":
            img_path = os.path.join(IMG_DIR, WORD_DATA['img1'])
            is_center = True
        elif scene == "sent1":
            img_path = create_text_card(WORD_DATA['sent1'], os.path.join(temp_dir, "sent1.png"))
        elif scene == "sent2":
            img_path = create_text_card(WORD_DATA['sent2'], os.path.join(temp_dir, "sent2.png"))
        elif scene == "img2":
            img_path = os.path.join(IMG_DIR, WORD_DATA['img2'])
            is_center = True

        if img_path and os.path.exists(img_path):
            print(f"   🎞 處理分鏡: {scene} ({start:.1f}s - {end:.1f}s)")
            p_img = Image.open(img_path)
            
            if is_center:
                # 圖片放置中央
                # 限制圖片大小不要超過螢幕太大
                clip_w = min(p_img.width, 800)
                clip = (ImageClip(img_path)
                        .resized(width=clip_w)
                        .with_start(start)
                        .with_duration(end - start)
                        .with_position(("center", "center")))
            else:
                # 文字與音標放置側邊
                tw = OVERLAY_WIDTH
                th = int(p_img.height * (tw / p_img.width))
                if th > MAX_H:
                    th = MAX_H
                    tw = int(p_img.width * (th / p_img.height))
                
                clip = (ImageClip(img_path)
                        .resized(width=tw)
                        .with_start(start)
                        .with_duration(end - start)
                        .with_position((SIDE_X, SIDE_Y)))
            
            overlay_clips.append(clip)

    # 5. 合成最終影片
    print("   🎥 正在渲染影片 (fps=24)...")
    final = CompositeVideoClip([base_clip] + overlay_clips)
    final.write_videofile(FINAL_OUTPUT, fps=24, logger=None)
    print(f"✅ 完成！Demo 影片已生成: {FINAL_OUTPUT}")

if __name__ == "__main__":
    make_demo()
