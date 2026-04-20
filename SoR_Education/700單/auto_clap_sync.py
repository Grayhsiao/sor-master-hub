import os
import ast
import pandas as pd
from pydub import AudioSegment
from matrix_stitcher import distribute_to_three_rows

CSV_FILE = "production_test.csv"
CLAP_DB_THRESHOLD = -16

def get_clap_timestamps(audio_path, threshold_db=CLAP_DB_THRESHOLD):
    print(f"   👏 [偵測] 掃描音檔拍手點 ({audio_path})...")
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"   ❌ 音檔讀取失敗: {e}")
        return []
        
    chunk_ms = 50
    timestamps = []
    last_clap = 0
    for i in range(0, len(audio), chunk_ms):
        chunk = audio[i:i+chunk_ms]
        if chunk.dBFS > threshold_db:
            # 確保兩個拍手之間相隔至少 1.5 秒，避免餘音誤判
            if (i - last_clap) > 1500:
                timestamps.append(i / 1000.0)
                last_clap = i
    
    # 返回找到的拍手點陣列
    return timestamps

def calculate_expected_scenes(row):
    """
    根據實際資料計算預期需要的拍手轉場
    回傳需要時間點的對應欄位名稱陣列
    """
    scenes = []
    # 1. 至少要切換到 全景 Matrix (第一拍)
    scenes.append("T_Matrix")
    
    # 2. 判斷音標組合有幾排 (由語調列出)
    intonation_str = str(row.get('語調', ''))
    intonation_list = list(intonation_str.replace(" ", "")) if intonation_str and intonation_str != 'nan' else []
    row_count = len(intonation_list) if intonation_list else 1
        
    for i in range(1, row_count + 1):
        scenes.append(f"T_Row{i}")
    
    # 3. 判斷後續附加內容
    if str(row.get('例句１', '')).strip() and str(row.get('例句１', '')).strip() != 'nan':
        scenes.append("T_Sent1")
    if str(row.get('圖片１', '')).strip() and str(row.get('圖片１', '')).strip() != 'nan':
        scenes.append("T_Img1")
    if str(row.get('例句２', '')).strip() and str(row.get('例句２', '')).strip() != 'nan':
        scenes.append("T_Sent2")
    if str(row.get('圖片２', '')).strip() and str(row.get('圖片２', '')).strip() != 'nan':
        scenes.append("T_Img2")
        
    return scenes

def process_sync():
    if not os.path.exists(CSV_FILE):
        print(f"❌ 找不到 {CSV_FILE}")
        return
        
    df = pd.read_csv(CSV_FILE)
    
    # 重置基本時間戳欄位，T_Row 等會隨著單字動態被建立或補上
    basic_cols = ["T_Matrix", "T_Sent1", "T_Img1", "T_Sent2", "T_Img2"]
    for col in basic_cols:
        if col not in df.columns:
            df[col] = ""

    for index, row in df.iterrows():
        word = str(row['單字'])
        audio_path = str(row.get('音檔路徑', ''))
        
        if not audio_path or not os.path.exists(audio_path):
            print(f"⚠️ 單字 [{word}] 的音檔不存在: {audio_path}")
            continue
            
        print(f"\n🎬 處理單字: {word}")
        expected_scenes = calculate_expected_scenes(row)
        print(f"   📋 預期拍手數: {len(expected_scenes)} 下 (排程: {', '.join(expected_scenes)})")
        
        claps = get_clap_timestamps(audio_path)
        print(f"   🔊 偵測到實際拍手: {len(claps)} 下 -> {claps}")
        
        if len(claps) < len(expected_scenes):
            print(f"   ⚠️ 警告: 拍手次數不足 ({len(claps)} < {len(expected_scenes)})。部分最後方的分鏡可能無法觸發。")
        elif len(claps) > len(expected_scenes):
            print(f"   ℹ️ 提示: 拍手次數過多 ({len(claps)} > {len(expected_scenes)})。多餘的拍手將被忽略。")
            
        # 依序填入 CSV
        for i, col_name in enumerate(expected_scenes):
            if i < len(claps):
                df.at[index, col_name] = claps[i]
            else:
                df.at[index, col_name] = "" # 沒拍到的留空
                
    # 儲存
    df.to_csv(CSV_FILE, index=False)
    print(f"\n✅ 拍手對位結果已更新回 {CSV_FILE}")

if __name__ == "__main__":
    # 使用 pydub 前可能需要讓系統認得 ffmpeg 
    os.environ["PATH"] += os.pathsep + "/usr/local/bin" + os.pathsep + "/opt/homebrew/bin"
    process_sync()
