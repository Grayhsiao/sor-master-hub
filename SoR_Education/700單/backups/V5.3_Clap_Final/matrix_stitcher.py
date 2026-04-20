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
        combined.paste(p, (x_offset, 0), p)
        x_offset += p.width
    return combined

def get_matrix_rows(minum_str, intonation_str="", max_w=800, row_h=145, include_intonation=True, top_padding=100):
    """
    解析 minum 與 intonation，產出音標 Row
    top_padding: 語調標記的上方留白
      - 全景(S2)用 15px (緊湊，三排塞進藍框)
      - 聚焦(S3-S5)用 100px (寬鬆，單排獨立展示)
    """
    try:
        data = ast.literal_eval(minum_str)
    except Exception as e:
        print(f"❌ Minum 解析失敗: {minum_str}, error: {e}")
        return [None, None, None]

    final_intonation = intonation_str if include_intonation else ""
    intonation_list = list(final_intonation.replace(" ", "")) if final_intonation else []
    
    rows_data = distribute_to_three_rows(data)
    row_images = []
    
    for r_idx, raw_row in enumerate(rows_data):
        items = []
        total_row_w = 0
        for group in raw_row:
            item_img = get_phonetic_image(group, target_h=row_h)
            if item_img:
                items.append(item_img)
                total_row_w += item_img.width
        
        if not items:
            row_images.append(None)
            continue
            
        actual_max_h = row_h + top_padding
        row_canvas = Image.new("RGBA", (total_row_w, actual_max_h), (0,0,0,0))
        
        # 1. 貼上音標 (靠底部對齊)
        curr_x = 0
        for itm in items:
            y_off = actual_max_h - itm.height
            row_canvas.paste(itm, (curr_x, y_off), itm)
            curr_x += itm.width
            
        # 移除了語調繪製，統一改由 get_intonation_layer 處理 (只畫在白板頂部)
            
        if total_row_w > max_w:
            ratio = max_w / total_row_w
            new_h = int(actual_max_h * ratio)
            row_canvas = row_canvas.resize((max_w, new_h), Image.Resampling.LANCZOS)
            
        row_images.append(row_canvas)
    
    return row_images

def get_intonation_layer(minum_str, intonation_str, max_w=700, row_h=145, target_height=25):
    """
    根據第一個 Row 的寬度與排版，產生獨立的語調圖層
    獨立放置在白板頂部 (Y_TOP 到 PH_Y 的空間)
    """
    if not intonation_str:
        return None
        
    try:
        data = ast.literal_eval(minum_str)
    except:
        return None
        
    intonation_list = list(intonation_str.replace(" ", ""))
    if not intonation_list: return None
    
    rows_data = distribute_to_three_rows(data)
    if not rows_data or not rows_data[0]: return None
    
    # 計算第一排的寬度特徵，用來定位語調
    raw_row = rows_data[0]
    items = []
    total_row_w = 0
    for group in raw_row:
        item_img = get_phonetic_image(group, target_h=row_h)
        if item_img:
            items.append(item_img)
            total_row_w += item_img.width
            
    if not items: return None
    
    layer = Image.new("RGBA", (total_row_w, target_height), (0,0,0,0))
    first_w = items[0].width
    start_center_x = first_w // 2
    step_w = first_w // 2
    
    for idx, code in enumerate(intonation_list):
        icon = get_intonation_icon(code, target_w=first_w)
        if icon:
            # 依據高度縮放 icon
            ratio = target_height / icon.height
            icon = icon.resize((int(icon.width * ratio), target_height), Image.Resampling.LANCZOS)
            
            tx = start_center_x + (idx * step_w) - (icon.width // 2)
            if tx + icon.width <= total_row_w:
                layer.paste(icon, (int(tx), 0), icon)
                
    if total_row_w > max_w:
        ratio = max_w / total_row_w
        layer = layer.resize((max_w, target_height), Image.Resampling.LANCZOS)
        
    return layer

def stitch_matrix_phonetics(minum_str, intonation_str="", max_w=700, row_h=145):
    """
    全景拼合：使用緊湊 padding (top_padding=15)
    三排放在 160px 間距內，總高 480px = 藍框高度 (630-150)
    """
    # 全景用緊湊 padding，每排 145+15=160px，剛好三排填滿 480px
    compact_padding = 15
    rows = get_matrix_rows(minum_str, intonation_str, max_w, row_h, 
                           include_intonation=True, top_padding=compact_padding)
    
    # 鎖定藍框內可用高度 480px (Y: 150 到 630)
    canvas_h = 480
    canvas_w = max_w
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
    
    # 三排固定位置：Y=0, 160, 320 (相對於 canvas 頂部)
    row_step = 160
    for i, r in enumerate(rows):
        if r:
            canvas.paste(r, (0, i * row_step), r)
            
    return canvas

if __name__ == "__main__":
    # 測試 beautiful 的語調標註: 1 . .
    beautiful_minum = "[[[1],[59,60]],[[15],[44]],[[4],[43]]]"
    result = stitch_matrix_phonetics(beautiful_minum, intonation_str="1..")
    if result:
        result.save("test_beautiful_matrix_intonation.png")
        print("✅ beautiful 語調測試圖已生成: test_beautiful_matrix_intonation.png")
