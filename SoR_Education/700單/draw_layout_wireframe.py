from PIL import Image, ImageDraw, ImageFont
import os

def draw_layout_wireframe(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ 找不到底圖: {input_path}")
        return

    # 1. 讀取並縮放至 1080x1920
    img = Image.open(input_path).convert("RGBA")
    target_w, target_h = 1080, 1920
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except:
        font = ImageFont.load_default()

    # --- 定義範圍 ---
    # 白板可用範圍: (200, 150) 到 (900, 630)
    wb_box = [200, 150, 900, 630]
    
    # 2. 畫出白板可用範圍 (藍色虛線框感)
    draw.rectangle(wb_box, outline=(0, 0, 255, 255), width=5)
    draw.text((210, 160), "Whiteboard Safe Zone", fill=(0, 0, 255, 255), font=font)

    # 3. 標註文字與圖片起點
    # 單字、音標、例句 X 起點 (X: 200)
    draw.line([(200, 150), (200, 800)], fill=(0, 255, 0, 255), width=3)
    draw.text((150, 650), "X:200 Align Left", fill=(0, 255, 0, 255), font=font)
    
    # 圖片 X, Y 起點 (X: 150, Y: 150)
    draw.ellipse([150-10, 150-10, 150+10, 150+10], fill=(255, 0, 255, 255))
    draw.text((10, 120), "Img Start (150, 150)", fill=(255, 0, 255, 255), font=font)

    # 4. 示意單字垂直中心
    center_y = (150 + 630) // 2
    draw.line([(200, center_y), (900, center_y)], fill=(255, 0, 0, 150), width=2)
    draw.text((600, center_y - 40), "Word Center Y", fill=(255, 0, 0, 255), font=font)

    # 5. 示意音標三排區域 (每排約 145px)
    for i in range(3):
        y_pos = 150 + (i * 160) # 加上一點間隔
        draw.rectangle([210, y_pos, 890, y_pos + 145], outline=(150, 150, 0, 150), width=2)
        draw.text((220, y_pos + 10), f"PH Row {i+1}", fill=(150, 150, 0, 255), font=font)

    # 儲存
    img.save(output_path)
    print(f"✅ 放樣確認圖已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    draw_layout_wireframe("avatar.png", "layout_wireframe.png")
