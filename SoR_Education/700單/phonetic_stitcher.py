import pandas as pd
import ast
import os
from PIL import Image

# 設定路徑
EXCEL_FILE = "字典底層資料 的副本.xlsx"
ASSETS_DIR = "drive-download-20260218T084106Z-1-001"
OUTPUT_DIR = "phonetic_output"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def stitch_phonetics(word, minum_str, direction="horizontal"):
    """
    將 minum 字串轉換為拼貼後的圖片。支援 'horizontal' (橫) 或 'vertical' (直)。
    """
    try:
        # 清洗字串，有時候 Excel 讀出來會帶有多餘括號或格式
        # 我們直接解析成 list
        data = ast.literal_eval(minum_str)
        # minum 通常是 [[[...]]] 三層結構，我們取出最內層的編號
        # 例如 [[[1],[45],[16]]] -> [[1], [45], [16]]
        symbols = data[0] if isinstance(data, list) and len(data) > 0 else []
        
        images = []
        for sym_list in symbols:
            # sym_list 可能是 [38, 25] 或 [1]
            for sym_id in sym_list:
                img_path = os.path.join(ASSETS_DIR, f"{sym_id}.png")
                if os.path.exists(img_path):
                    images.append(Image.open(img_path).convert("RGBA"))
                else:
                    print(f"  ⚠️ 找不到圖檔: {img_path}")

        if not images:
            return None

        if direction == "horizontal":
            # 橫向拼貼
            total_width = sum(img.width for img in images) + (len(images) - 1) * 5 # 加一點間距
            max_height = max(img.height for img in images)
            combined_img = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))
            current_x = 0
            for img in images:
                # 置中貼上 (高度方向)
                y_offset = (max_height - img.height) // 2
                combined_img.paste(img, (current_x, y_offset), img)
                current_x += img.width + 5
        else:
            # 縱向拼貼 (直的排列)
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images) + (len(images) - 1) * 10
            combined_img = Image.new("RGBA", (max_width, total_height), (0, 0, 0, 0))
            current_y = 0
            for img in images:
                # 置中貼上 (寬度方向)
                x_offset = (max_width - img.width) // 2
                combined_img.paste(img, (x_offset, current_y), img)
                current_y += img.height + 10
            
        output_path = os.path.join(OUTPUT_DIR, f"{word}_phonetic.png")
        combined_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"  ❌ 處理 {word} 時發生錯誤: {e}")
        return None

# --- 測試執行 ---
try:
    df = pd.read_excel(EXCEL_FILE)
    # 取幾個 700 單樣本
    samples = df[df['700Id'].notna()].head(5)
    
    print(f"🚀 開始測試音標拼貼 (輸出至 {OUTPUT_DIR}):")
    for _, row in samples.iterrows():
        word = str(row['word'])
        minum = str(row['minum'])
        if minum and minum != 'nan' and minum != '專利音標':
            result = stitch_phonetics(word, minum, direction="vertical")
            if result:
                print(f"  ✅ {word} -> {result}")
except Exception as e:
    print(f"發生錯誤: {e}")
