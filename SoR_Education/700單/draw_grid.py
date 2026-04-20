from PIL import Image, ImageDraw, ImageFont
import os

def draw_grid_on_avatar(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ 找不到底圖: {input_path}")
        return

    # 1. 讀取並縮放至 1080x1920 (維持腳本邏輯)
    img = Image.open(input_path).convert("RGBA")
    target_w, target_h = 1080, 1920
    
    # 計算縮放比例
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    draw = ImageDraw.Draw(img)
    
    # 嘗試載入字體
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        big_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except:
        font = ImageFont.load_default()
        big_font = ImageFont.load_default()

    # 2. 畫網格
    grid_step = 100
    sub_step = 50

    # 畫垂直線 (X 軸)
    for x in range(0, target_w + 1, sub_step):
        width = 2 if x % grid_step == 0 else 1
        color = (255, 0, 0, 150) if x % grid_step == 0 else (255, 0, 0, 50)
        draw.line([(x, 0), (x, target_h)], fill=color, width=width)
        if x % grid_step == 0:
            draw.text((x + 5, 20), f"X:{x}", fill=(255, 0, 0, 255), font=font)

    # 畫水平線 (Y 軸)
    for y in range(0, target_h + 1, sub_step):
        width = 2 if y % grid_step == 0 else 1
        color = (255, 0, 0, 150) if y % grid_step == 0 else (255, 0, 0, 50)
        draw.line([(0, y), (target_w, y)], fill=color, width=width)
        if y % grid_step == 0:
            draw.text((10, y + 5), f"Y:{y}", fill=(255, 0, 0, 255), font=font)

    # 3. 在交點標註大數字
    for x in range(200, target_w, 200):
        for y in range(200, target_h, 200):
            draw.ellipse([x-3, y-3, x+3, y+3], fill="red")
            draw.text((x+5, y+5), f"{x},{y}", fill=(0, 0, 255, 180), font=font)

    # 儲存
    img.save(output_path)
    print(f"✅ 座標地圖已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    draw_grid_on_avatar("avatar.png", "avatar_with_grid.png")
