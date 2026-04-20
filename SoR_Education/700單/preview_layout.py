from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
from matrix_stitcher import stitch_matrix_phonetics

def get_font(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except:
        return ImageFont.load_default()

def create_preview_frame(content_type, content_data, output_name):
    # 1. 準備底圖
    base = Image.open("avatar.png").convert("RGBA")
    base = base.resize((1080, 1920), Image.Resampling.LANCZOS)
    
    # 2. 準備佈局層 (用於背板與內容)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 定義安全區 (Safe Zone) 與背板
    safe_zone = [200, 150, 900, 630]
    # 半透明白色背板 (Alpha=60, 拿掉藍色邊框)
    draw.rectangle(safe_zone, fill=(255, 255, 255, 60))
    
    # 3. 根據類型渲染內容
    if content_type == "word":
        # 單字居中於安全區
        font = get_font(145)
        text = str(content_data)
        # 計算文字尺寸以居中
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        center_x = (safe_zone[0] + safe_zone[2]) // 2 - w // 2
        center_y = (safe_zone[1] + safe_zone[3]) // 2 - h // 2
        draw.text((center_x, center_y), text, fill=(0, 0, 0, 255), font=font)
        
    elif content_type == "phonetics":
        # 音標矩陣
        ph_img = stitch_matrix_phonetics(content_data)
        if ph_img:
            # 貼在安全區內 X:200, Y:150
            overlay.paste(ph_img, (200, 150), ph_img)
            
    elif content_type == "text":
        # 字義或例句 (X:200, Size:70, 自動換行)
        font = get_font(70)
        lines = textwrap.wrap(content_data, width=25) # 寬度調整為 25 字符
        y_offset = 310 # 建議起始位置
        for line in lines:
            draw.text((200, y_offset), line, fill=(0, 0, 0, 255), font=font)
            y_offset += 80

    elif content_type == "image":
        # 圖片放樣 (150, 150)
        img_temp = Image.new("RGBA", (400, 400), (200, 200, 200, 200)) # 模擬圖片
        draw_temp = ImageDraw.Draw(img_temp)
        draw_temp.text((10, 180), "SAMPLE IMAGE", fill="white", font=get_font(40))
        overlay.paste(img_temp, (150, 150), img_temp)

    # 4. 合併並儲存
    final = Image.alpha_composite(base, overlay)
    final.save(output_name)
    print(f"✅ 預覽圖已生成: {output_name}")

if __name__ == "__main__":
    # 產出五張測試圖
    create_preview_frame("word", "beautiful", "preview_1_word.png")
    create_preview_frame("phonetics", "[[[1],[59,60]],[[15],[44]],[[4],[43]]]", "preview_2_ph.png")
    create_preview_frame("text", "adj. 美麗的，漂亮的；美好的", "preview_3_meaning.png")
    create_preview_frame("text", "She is a beautiful girl with a kind heart.", "preview_4_sent.png")
    create_preview_frame("image", None, "preview_5_img.png")
