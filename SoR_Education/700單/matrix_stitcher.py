import os
import json
import ast
from PIL import Image, ImageDraw
from matrix_layout_logic import distribute_to_three_rows

# 音標路徑
PHONETIC_DIR = "drive-download-20260218T084106Z-1-001"

# 語調符號映射
INTONATION_MAP = {
    '1': "語調符號-一聲.png",
    '4': "語調符號-4聲.png",
    '.': "語調符號-輕聲.png"
}

def get_intonation_icon(code, target_w):
    """取得並縮放語調符號"""
    fname = INTONATION_MAP.get(code)
    if not fname: return None
    path = os.path.join(PHONETIC_DIR, fname)
    if os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        # 語調符號縮小至適當寬度 (約音標塊的 40%)
        icon_w = int(target_w * 0.45)
        ratio = icon_w / img.width
        return img.resize((icon_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
    return None

def get_phonetic_image(symbol_ids, target_h=145):
    """
    將一組 ID 拼成一個物件，並確保高度不超過 target_h
    """
    if isinstance(symbol_ids, int):
        symbol_ids = [symbol_ids]
    
    parts = []
    total_w = 0
    max_h = 0
    
    for sid in symbol_ids:
        path = os.path.join(PHONETIC_DIR, f"{sid}.png")
        if os.path.exists(path):
            p_img = Image.open(path).convert("RGBA")
            if p_img.height > target_h:
                ratio = target_h / p_img.height
                p_img = p_img.resize((int(p_img.width * ratio), target_h), Image.Resampling.LANCZOS)
            
            parts.append(p_img)
            total_w += p_img.width
            max_h = max(max_h, p_img.height)
        else:
            print(f"⚠️ 找不到音標檔案: {path}")
            
    if not parts:
        return None
        
    combined = Image.new("RGBA", (total_w, max_h), (0,0,0,0))
    x_offset = 0
    for p in parts:
        # 下標齊平 (針對相同高度通常等同於直接貼上)
        y_off = max_h - p.height
        combined.paste(p, (x_offset, y_off), p)
        x_offset += p.width
    return combined

from matrix_layout_logic import distribute_by_syllables

def get_matrix_rows(minum_str, intonation_str="", max_w=700, target_h=145, top_padding=100):
    """
    解析 minum 與 intonation，根據語調符號數量產出動態排數
    每排的最左側會放置對應的語調符號。
    """
    try:
        data = ast.literal_eval(minum_str)
    except Exception as e:
        print(f"❌ Minum 解析失敗: {minum_str}, error: {e}")
        return []

    intonation_list = list(intonation_str.replace(" ", "")) if intonation_str else []
    num_syllables = len(intonation_list) if intonation_list else 1
    
    # 動態計算高度，確保排數多時可以塞入 480px 的可用高度 (15px padding)
    # max 480 = n * row_h + (n-1) * 15  => row_h = (480 - (n-1)*15) / n
    avail_h = (480 - (num_syllables - 1) * 15) // num_syllables
    row_h = min(target_h, max(avail_h, 60)) # 限制最大 145，最小 60

    rows_data = distribute_by_syllables(data, num_syllables)
    row_images = []
    
    for r_idx, raw_row in enumerate(rows_data):
        items = []
        total_content_w = 0
        actual_max_h = row_h
        
        for group in raw_row:
            item_img = get_phonetic_image(group, target_h=row_h)
            if item_img:
                items.append(("phonetic", item_img))
                total_content_w += item_img.width
                actual_max_h = max(actual_max_h, item_img.height)
        
        if not items:
            row_images.append(None)
            continue
            
        # 如果單排原始寬度就超標，先算好縮放比例
        scale_ratio = 1.0
        if total_content_w > max_w:
            scale_ratio = max_w / total_content_w

        # 為了維持最高品質，我們先畫在剛好大小的 raw_canvas，再縮放並貼到 max_w 的畫布
        raw_canvas_h = actual_max_h + top_padding
        raw_canvas = Image.new("RGBA", (total_content_w, raw_canvas_h), (0,0,0,0))
        
        # 靠底對齊貼上
        curr_x = 0
        for itype, itm in items:
            y_off = raw_canvas_h - itm.height
            raw_canvas.paste(itm, (curr_x, y_off), itm)
            curr_x += itm.width
            
        if scale_ratio < 1.0:
            new_h = int(raw_canvas_h * scale_ratio)
            raw_canvas = raw_canvas.resize((max_w, new_h), Image.Resampling.LANCZOS)
            
        # 建立滿寬畫布，將內容「水平置中」貼上
        final_h = raw_canvas.height
        row_canvas = Image.new("RGBA", (max_w, final_h), (0,0,0,0))
        paste_x = (max_w - raw_canvas.width) // 2
        row_canvas.paste(raw_canvas, (paste_x, 0), raw_canvas)
            
        row_images.append(row_canvas)
    
    return row_images

def stitch_matrix_phonetics(minum_str, intonation_str="", max_w=700, target_h=145):
    """
    全景拼合：將 N 排固定在三個網格區域的正中間，保證對齊 3-Row Grid 的精確基準線。
    白板有效高度為 505px (Y: 125 ~ 630)，切出三等份。
    第一格中心: Y = 84
    第二格中心: Y = 252 (如果只有一排，強制置中於此)
    第三格中心: Y = 421
    """
    rows = get_matrix_rows(minum_str, intonation_str, max_w, target_h, top_padding=0)
    valid_rows = [r for r in rows if r]
    
    total_w = max_w
    total_h = 505
    canvas = Image.new("RGBA", (total_w, total_h), (0,0,0,0))

    if not valid_rows:
        return canvas
        
    # 畫語調 (在整個畫布最上方，置中，避開 6px 邊框)
    intonation_list = list(intonation_str.replace(" ", "")) if intonation_str else []
    if intonation_list:
        into_icons = []
        into_h = 18 # 稍微縮小一點點以完美塞入 25px 的頂部空間
        for code in intonation_list:
            fname = INTONATION_MAP.get(code)
            if fname:
                path = os.path.join(PHONETIC_DIR, fname)
                if os.path.exists(path):
                    img = Image.open(path).convert("RGBA")
                    ratio = into_h / img.height
                    into_icon = img.resize((int(img.width * ratio), into_h), Image.Resampling.LANCZOS)
                    into_icons.append(into_icon)
        if into_icons:
            gap = 30
            total_into_w = sum(icon.width for icon in into_icons) + gap * (len(into_icons) - 1)
            into_x = (total_w - total_into_w) // 2
            into_y = 7 # 避開 6px 邊框 (125+7=132)，且不會遮到 150 開始的音標排
            for icon in into_icons:
                canvas.paste(icon, (into_x, into_y), icon)
                into_x += icon.width + gap

    num_syllables = len(valid_rows)
    # y 軸網格中心點 (符合 PH Row 1: 150, 2: 310, 3: 470 標準)
    # 相對於 Y=125 的位置: (150+72.5-125)=97.5, (310+72.5-125)=257.5, (470+72.5-125)=417.5
    grid_centers = [97, 257, 417]
    
    if num_syllables == 1:
        # 單排強制放正中央 (格 2)
        r_img = valid_rows[0]
        paste_y = grid_centers[1] - (r_img.height // 2)
        canvas.paste(r_img, (0, paste_y), r_img)
    else:
        # 依序放到對應格子 (如果是 2 排放 1, 2；3 排放 1, 2, 3)
        for i, r_img in enumerate(valid_rows):
            if i >= 3: break # 最多三排
            paste_y = grid_centers[i] - (r_img.height // 2)
            canvas.paste(r_img, (0, paste_y), r_img)
        
    return canvas

if __name__ == "__main__":
    # 測試 beautiful 的語調標註: 1 . .
    beautiful_minum = "[[[1],[59,60]],[[15],[44]],[[4],[43]]]"
    result = stitch_matrix_phonetics(beautiful_minum, intonation_str="1..")
    if result:
        result.save("test_beautiful_matrix_intonation.png")
        print("✅ beautiful 語調測試圖已生成: test_beautiful_matrix_intonation.png")
