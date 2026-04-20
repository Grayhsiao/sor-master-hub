from moviepy import VideoFileClip
from PIL import Image, ImageDraw, ImageFont
import os

def draw_grid_on_frame(pil_img):
    draw = ImageDraw.Draw(pil_img)
    w, h = pil_img.size
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font = ImageFont.load_default()

    grid_step = 100
    for x in range(0, w + 1, grid_step):
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 100), width=1)
        draw.text((x + 2, 5), str(x), fill=(255, 0, 0, 200), font=font)
        
    for y in range(0, h + 1, grid_step):
        draw.line([(0, y), (w, y)], fill=(255, 0, 0, 100), width=1)
        draw.text((5, y + 2), str(y), fill=(255, 0, 0, 200), font=font)
    
    return pil_img

def generate_debug_images(video_path):
    if not os.path.exists(video_path):
        print(f"❌ 找不到影片: {video_path}")
        return

    clip = VideoFileClip(video_path)
    # 定義要調試的時間點 (參考 demo_last_v1.py 的分配)
    debug_times = {
        "1_word": 8,
        "2_ph": 24,
        "3_meaning": 40,
        "4_img_bug": 56,
        "5_sentence": 72,
        "6_sent2": 90,
        "7_img2": 106
    }

    for name, t in debug_times.items():
        print(f"📸 正在擷取 {name} (t={t}s)...")
        frame = clip.get_frame(t)
        img = Image.fromarray(frame)
        img_grid = draw_grid_on_frame(img)
        output_name = f"debug_grid_{name}.png"
        img_grid.save(output_name)
        print(f"   ✅ 已儲存: {output_name}")

    clip.close()

if __name__ == "__main__":
    generate_debug_images("final_last_demo.mp4")
