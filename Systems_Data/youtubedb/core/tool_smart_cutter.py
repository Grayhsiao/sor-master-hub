"""
=============================================================================
✂️ AI 智慧剪輯刀 V2 (字幕對齊精準版)
=============================================================================
[改進點]
1. 拒絕 AI 瞎猜時間：改為讓 AI 選擇 SRT 的「行數 ID」。
2. 完美斷句：直接使用 SRT 內建的精準時間碼，確保不會切在字中間。
3. 智能緩衝：前後自動多留 0.2 秒，讓聲音聽起來更自然。
=============================================================================
"""

import os
import re
import subprocess
import json
from openai import OpenAI

# 📂 檔案路徑
SOURCE_VIDEO = "downloaded_files/full_video.mp4"   # 記得要用有畫面的 mp4
SOURCE_SRT = "sources/jAgRs8mwg20_中英字幕｜What is SoR ｜背單字前你應該先知道的3步驟｜科普系列｜蕭博士 SoR 美語.srt"
OUTPUT_FILENAME = "final_clip_v2.mp4"

# 🎯 你的問題
USER_QUERY = "什麼是 SoR？它的定義是什麼？"

# API Key 從環境變數讀取
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', '').strip())

def parse_srt_structured(srt_path):
    """
    將 SRT 解析為結構化列表：
    [
      {'id': 1, 'start': '00:00:00,000', 'end': '00:00:05,000', 'text': 'What is SoR?'}, 
      ...
    ]
    """
    if not os.path.exists(srt_path):
        return None
        
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 使用正則表達式拆解 SRT
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
    matches = pattern.findall(content)
    
    srt_data = []
    for m in matches:
        srt_data.append({
            "id": int(m[0]),
            "start": m[1],
            "end": m[2],
            "text": m[3].strip().replace('\n', ' ')
        })
    return srt_data

def get_best_segment_by_id(srt_data, query):
    """讓 AI 挑選『哪幾行』字幕最能回答問題"""
    print(f"🤖 AI 正在閱讀 {len(srt_data)} 行字幕，尋找答案...")

    # 為了讓 AI 好讀，我們把 SRT 轉成 "ID: 文字" 的格式
    srt_text_preview = "\n".join([f"ID {item['id']}: {item['text']}" for item in srt_data])

    prompt = f"""
    你是專業的影片剪輯師。
    請根據使用者的問題，從下方的字幕列表中，選出**一段連續的字幕 ID 範圍**。

    【使用者問題】：{query}

    【字幕列表】：
    {srt_text_preview[:15000]} 
    (內容過長已截斷)

    【選擇規則】：
    1. **完整性優先**：必須包含完整的句子，不要只選半句。
    2. **上下文**：如果有「因為...所以...」的邏輯，請把前後句都選進來。
    3. **回傳格式**：請回傳 JSON，包含開始的 ID (start_id) 和結束的 ID (end_id)。

    範例回傳：
    {{
        "start_id": 12,
        "end_id": 15,
        "reason": "這段完整解釋了定義"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def time_str_to_seconds(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def cut_video_precise(source_file, start_time, end_time, output_file):
    print(f"🔪 精準切割: {start_time} -> {end_time}")
    
    # 微調：前後多留 0.1 秒，防止聲音太乾
    s_sec = max(0, time_str_to_seconds(start_time) - 0.1)
    e_sec = time_str_to_seconds(end_time) + 0.1
    duration = e_sec - s_sec
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(s_sec),
        "-t", str(duration),
        "-i", source_file,
        "-c:v", "libx264", # 重新編碼以確保幀準確 (雖然慢一點點但更精準)
        "-c:a", "aac",
        "-strict", "experimental",
        output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ 影片已生成: {output_file}")
    except Exception as e:
        print(f"❌ 切割失敗: {e}")

# ==========================================
# 主程式
# ==========================================
srt_data = parse_srt_structured(SOURCE_SRT)

if srt_data:
    # 1. 問 AI 要選哪幾行
    selection = get_best_segment_by_id(srt_data, USER_QUERY)
    
    if selection:
        s_id = selection['start_id']
        e_id = selection['end_id']
        
        # 2. 查出這幾行對應的時間
        # (注意 SRT ID 通常從 1 開始，List index 從 0 開始，要做轉換)
        # 簡單搜尋法：
        start_item = next((x for x in srt_data if x['id'] == s_id), None)
        end_item = next((x for x in srt_data if x['id'] == e_id), None)
        
        if start_item and end_item:
            print(f"\n🎯 AI 選中段落 (ID {s_id} ~ {e_id})：")
            print(f"   📝 開始句: {start_item['text']}")
            print(f"   📝 結束句: {end_item['text']}")
            print(f"   💡 理由: {selection['reason']}\n")
            
            # 3. 執行切割
            if os.path.exists(SOURCE_VIDEO):
                cut_video_precise(SOURCE_VIDEO, start_item['start'], end_item['end'], OUTPUT_FILENAME)
            else:
                print(f"❌ 找不到影片: {SOURCE_VIDEO}")
        else:
            print("❌ 找不到對應的字幕 ID")