import os
import time
import requests
import textwrap
import pandas as pd
import ast
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, ColorClip, CompositeVideoClip, AudioFileClip
from pydub import AudioSegment
# 如果是 v2.x 也可以嘗試從各別模組匯入，但 moviepy 通常支援直接從頂層匯入常用類別

# ================= ⚙️ 設定區域 =================

# --- 🔥 D-ID 開關 ---
ENABLE_DID = False 

DID_API_KEY = "您的_DID_API_KEY_貼在這裡"
DID_URL = "https://api.d-id.com/talks"

# --- 檔案與路徑設定 ---
EXCEL_FILE = "字典底層資料 的副本.xlsx" 
ASSETS_DIR = "drive-download-20260218T084106Z-1-001"
OUTPUT_DIR = "output_videos"
PHONETIC_DIR = "phonetic_output"

# --- 📊 Excel 欄位定義 (博士未來更換表格時，改這裡即可) ---
COL_WORD = "word"           # 單字
COL_MINUM = "minum"         # 專利音標編號
COL_MEANING = "Chinese"     # 單字意思 (目前對應 Chinese 欄位)
COL_SENT1 = "Sentence1"     # 例句1 (如果您之後的表格欄位名不同，請修改此處)
COL_SENT2 = "Sentence2"     # 例句2
COL_ORDER = "Order"         # 劇本順序 (word ph01 sent1 ...)
COL_AVATAR = "Avatar"       # 指定 D-ID 用的底圖 (如 avatar.png)

if not os.path.exists(PHONETIC_DIR):
    os.makedirs(PHONETIC_DIR)

# --- 博士指定的視覺參數 ---
OVERLAY_WIDTH = 500  # 博士要求寬度變 500
OVERLAY_Y = 500      # 博士要求 Y = 500
BG_IMAGE_NAME = "avatar.png" # 博士指定底圖

# ===============================================

# 引入之前的音標拼貼邏輯
def stitch_phonetics_vertical(word, minum_str):
    """橫向轉換為縱向拼貼，支援博士要求的垂直排列"""
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
        
        # 縱向排列
        max_w = max(img.width for img in images)
        total_h = sum(img.height for img in images) + (len(images)-1)*20
        combined = Image.new("RGBA", (max_w, total_h), (0,0,0,0))
        curr_y = 0
        for img in images:
            x_off = (max_w - img.width) // 2
            combined.paste(img, (x_off, curr_y), img)
            curr_y += img.height + 20
        
        out_path = os.path.join(PHONETIC_DIR, f"{word}_vert.png")
        combined.save(out_path)
        return out_path
    except: return None

def get_best_font(size):
    # macOS 預設字體路徑
    paths = ["/System/Library/Fonts/PingFang.ttc", "/Library/Fonts/Arial Unicode.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_text_card_vertical(text, output_path, is_title=False):
    """針對 500 寬度的縱向文字卡"""
    width, height = 500, 1000 # 假設一個區塊長度
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_size = 80 if is_title else 60
    font = get_best_font(font_size)
    
    # 縱向文字處理：如果是單字，我們讓它一個字母一排，或者維持 wrap
    lines = textwrap.wrap(str(text), width=5) # 500 寬度限制字數
    
    curr_y = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((width - w) // 2, curr_y), line, font=font, fill=(0,0,0,255))
        curr_y += font_size + 10
    
    # 自動裁切到有內容的區域
    img = img.crop((0, 0, width, curr_y + 20))
    img.save(output_path)
    return output_path

def get_clap_timestamps(audio_path, threshold_db=-16):
    print(f"   👏 [偵測] 正在分析拍手點...")
    audio = AudioSegment.from_file(audio_path)
    chunk_ms = 50
    timestamps = [0]
    last_clap = 0
    for i in range(0, len(audio), chunk_ms):
        chunk = audio[i:i+chunk_ms]
        if chunk.dBFS > threshold_db:
            if (i - last_clap) > 1500:
                timestamps.append(i / 1000.0)
                last_clap = i
    timestamps.append(len(audio) / 1000.0)
    return timestamps

def make_integrated_video_batch(limit=2):
    """依照 Excel 順序批量生產影片成品"""
    print(f"📂 讀取 Excel 並開始生產 (D-ID 開關: {ENABLE_DID})")
    # 讀取 Excel，支援量產清單或原始資料庫
    df = pd.read_excel(EXCEL_FILE).fillna("")
    
    # 智慧過濾：如果第一行是標頭說明（例如 word 欄位內容就是 "單字"），則跳過
    if not df.empty and str(df.iloc[0].get(COL_WORD, "")).strip() == "單字":
        df = df.iloc[1:]
    
    # 清理：移除任何 word 欄位為空的或仍帶有 "單字" 字樣的殘留列
    df = df[df[COL_WORD].apply(lambda x: str(x).strip() != "" and str(x).strip() != "單字")]
    
    # 建立暫存圖檔目錄
    temp_img_dir = "temp_gen_images"
    if not os.path.exists(temp_img_dir): os.makedirs(temp_img_dir)

    for idx, row in df.head(limit).iterrows():
        word = str(row['word']).strip()
        if not word: continue
        print(f"\n🎬 正在製作: {word}")

        # 1. 匹配音檔 (假設 mp3 存放在 ASSETS_DIR)
        audio_path = os.path.join(ASSETS_DIR, f"{word}.mp3")
        if not os.path.exists(audio_path):
            audio_path = os.path.join(ASSETS_DIR, f"{word.lower()}.mp3")
        
        has_real_audio = os.path.exists(audio_path)
        
        # 2. 準備拍手分鏡時間點與音軌
        if has_real_audio:
            try:
                timestamps = get_clap_timestamps(audio_path)
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
            except:
                print("   ⚠️ 拍手偵測失敗，使用均分分鏡。")
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                num_scenes = len(str(row.get(COL_ORDER, 'word ph01 Chinese')).split())
                timestamps = [i * (duration/num_scenes) for i in range(num_scenes)] + [duration]
        else:
            print(f"   ⚠️ 找不到音檔 {word}.mp3，進入靜音示範模式。")
            duration = 5.0
            order_list = str(row.get(COL_ORDER, 'word ph01 Chinese')).split()
            num_scenes = len(order_list)
            # 確保有足夠的時間點給所有分鏡
            timestamps = [i * (duration/num_scenes) for i in range(num_scenes)] + [duration]
            audio_clip = None
        # 3. 準備底圖影片 (avatar.png)
        base_clip = ImageClip(BG_IMAGE_NAME).with_duration(duration)
        base_clip = base_clip.resized(height=1920)
        if base_clip.w < 1080: base_clip = base_clip.resized(width=1080)
        base_clip = base_clip.cropped(x_center=base_clip.w/2, y_center=base_clip.h/2, width=1080, height=1920)
        
        if audio_clip:
            base_clip = base_clip.with_audio(audio_clip)

        # 4. 根據順序 (Order) 生成疊加層
        # 如果 Excel 中沒有 Order 欄位，我們預設跑: 單字 -> 音標 -> 字義
        order_list = str(row.get('Order', 'word ph01 Chinese')).split()
        if not order_list: order_list = ["word", "ph01", "Chinese"]
        
        overlay_clips = []
        MAX_H = int(1920 * 0.4) # 限高 40%
        
        # 確保 minum 欄位正確 (COL_MINUM 預設為 "minum")
        minum_data = row.get(COL_MINUM, "")
        
        for i, scene in enumerate(order_list):
            if i >= len(timestamps) - 1: break
            start, end = timestamps[i], timestamps[i+1]
            
            img_path = None
            if scene.lower() == "word":
                img_path = create_text_card_vertical(word, os.path.join(temp_img_dir, f"{word}_word.png"), is_title=True)
            elif "ph" in scene.lower() or "音標" in scene:
                img_path = stitch_phonetics_vertical(word, minum_data)
            elif scene.lower() in ["def", "意思", "meaning", "chinese"]:
                img_path = create_text_card_vertical(row.get(COL_MEANING, ''), os.path.join(temp_img_dir, f"{word}_def.png"))
            elif scene.lower() in ["sent1", "例句1", "s1"]:
                img_path = create_text_card_vertical(row.get(COL_SENT1, ''), os.path.join(temp_img_dir, f"{word}_s1.png"))
            elif scene.lower() in ["sent2", "例句2", "s2"]:
                img_path = create_text_card_vertical(row.get(COL_SENT2, ''), os.path.join(temp_img_dir, f"{word}_s2.png"))
            
            if img_path and os.path.exists(img_path):
                print(f"   🖼 產生分鏡圖卡: {scene} -> {img_path} (內容: {os.path.basename(img_path)})")
                # 智慧縮放佈局
                p_img = Image.open(img_path)
                tw = OVERLAY_WIDTH
                th = int(p_img.height * (tw / p_img.width))
                if th > MAX_H:
                    th = MAX_H
                    tw = int(p_img.width * (th / p_img.height))
                
                # 靠左對位避開人物臉部
                tx, ty = 150, 450
                
                clip = (ImageClip(img_path)
                        .resized(width=tw)
                        .with_start(start)
                        .with_duration(end - start)
                        .with_position((tx, ty)))
                overlay_clips.append(clip)

        # 5. 合成最終影片
        final = CompositeVideoClip([base_clip] + overlay_clips)
        output_name = f"final_{word}.mp4"
        final.write_videofile(output_name, fps=24, logger=None)
        print(f"   ✅ 完成！成品位於: {output_name}")

if __name__ == "__main__":
    # 測試一支影片
    make_integrated_video_batch(limit=1)
LineOffset: 0
