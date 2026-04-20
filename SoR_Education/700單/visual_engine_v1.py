from PIL import Image
import os

# 設定路徑
BG_IMAGE = "/Users/gray/.gemini/antigravity/brain/d657c0e7-19e0-4060-8020-f0e1a493d5ec/bg_warm_classroom_1771406534358.png"
PHONETIC_IMAGE = "phonetic_output/bed_phonetic.png"
OUTPUT_PREVIEW = "visual_demo_bed.png"

def create_visual_demo():
    if not os.path.exists(BG_IMAGE) or not os.path.exists(PHONETIC_IMAGE):
        print("❌ 找不到背景或音標圖檔")
        return

    # 1. 讀取背景並調整大小 (確保是 1080x1920)
    bg = Image.open(BG_IMAGE).convert("RGBA")
    bg = bg.resize((1080, 1920))

    # 2. 讀取音標圖
    phonetic = Image.open(PHONETIC_IMAGE).convert("RGBA")
    
    # 3. 依照博士指示：寬度 500，並轉為縱向排列
    max_w = 500 
    ratio = max_w / phonetic.width
    new_h = int(phonetic.height * ratio)
    phonetic = phonetic.resize((max_w, new_h))
    print(f"   🔍 音標縱向最終尺寸: {max_w}x{new_h}")

    # 4. 調整音標位置 (博士指定 Y=500)
    target_x = (1080 - max_w) // 2
    target_y = 500 
    print(f"   📍 貼放座標: ({target_x}, {target_y})")
    
    bg.paste(phonetic, (target_x, target_y), phonetic)

    # 5. 儲存結果 (更新檔名為 vertical 版)
    OUTPUT_PREVIEW_VERT = "visual_demo_bed_vertical.png"
    bg.save(OUTPUT_PREVIEW_VERT)
    print(f"✅ 視覺示範已生成: {OUTPUT_PREVIEW_VERT}")

if __name__ == "__main__":
    create_visual_demo()
LineOffset: 0
