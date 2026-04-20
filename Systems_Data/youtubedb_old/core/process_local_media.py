import os
import subprocess
import argparse
import re
import time
from datetime import timedelta
from utils import transcribe_audio_to_srt, generate_sor_content, clean_srt_to_text
from config import SOURCE_DIR, DOWNLOAD_DIR

def shift_srt_time(srt_content, offset_seconds):
    """將 SRT 內容中的所有時間戳偏移指定的秒數"""
    if offset_seconds == 0:
        return srt_content
    
    def shift_match(match):
        time_str = match.group(0)
        try:
            h, m, s = time_str.replace(',', '.').split(':')
            t = timedelta(hours=int(h), minutes=int(m), seconds=float(s))
            new_t = t + timedelta(seconds=offset_seconds)
            total_seconds = new_t.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            return f"{hours:02}:{minutes:02}:{seconds:06.3f}".replace('.', ',')
        except:
            return time_str
    return re.sub(r'\d{2}:\d{2}:\d{2},\d{3}', shift_match, srt_content)

def get_segment_start_time(segment_filename):
    match = re.search(r'seg_(\d+)', segment_filename)
    if match:
        return int(match.group(1)) * 1200
    return 0

def process_local_video(video_path, model_name="gemini"):
    if not os.path.exists(video_path):
        print(f"❌ 找不到檔案: {video_path}")
        return

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    print(f"\n🎬 開始處理影片: {base_name}")

    audio_path = os.path.join(DOWNLOAD_DIR, f"{base_name}.mp3")
    if not os.path.exists(audio_path):
        print(f"🎵 正在提取音訊...")
        try:
            subprocess.run([
                'ffmpeg', '-i', video_path, 
                '-vn', '-acodec', 'libmp3lame', '-q:a', '6',
                audio_path
            ], check=True, capture_output=True)
            print(f"✅ 音訊已提取: {audio_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg 錯誤: {e.stderr.decode()}")
            return
    
    srt_path = os.path.join(SOURCE_DIR, f"{base_name}.srt")
    if not os.path.exists(srt_path):
        file_size = os.path.getsize(audio_path)
        max_size = 24.5 * 1024 * 1024 
        
        if file_size > max_size:
            print(f"⚠️ 檔案過大 ({file_size/1024/1024:.1f}MB)，啟動自動分割轉譯流程...")
            segment_pattern = os.path.join(DOWNLOAD_DIR, f"{base_name}_seg_%03d.mp3")
            subprocess.run([
                'ffmpeg', '-i', audio_path, 
                '-f', 'segment', '-segment_time', '1200', 
                '-c', 'copy', segment_pattern
            ], check=True, capture_output=True)
            
            segments = sorted([f for f in os.listdir(DOWNLOAD_DIR) if re.match(re.escape(base_name) + r"_seg_\d+\.mp3", f)])
            print(f"📂 發現 {len(segments)} 個音訊片段。")
            
            full_srt = ""
            for seg in segments:
                seg_path = os.path.join(DOWNLOAD_DIR, seg)
                if not os.path.exists(seg_path):
                    print(f"❌ 片段遺失: {seg_path}")
                    continue
                
                offset = get_segment_start_time(seg)
                print(f"✍️ 正在轉譯片段 (偏移 {offset}s): {seg}...")
                
                seg_srt = transcribe_audio_to_srt(seg_path)
                if "Error" in seg_srt:
                    print(f"❌ 片段 {seg} 轉譯失敗: {seg_srt}")
                    full_srt += f"\n\n[TRANSCRIPTION ERROR IN {seg}]\n\n"
                else:
                    shifted_srt = shift_srt_time(seg_srt, offset)
                    full_srt += shifted_srt + "\n\n"
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(full_srt)
            print(f"✅ 合併轉譯完成！逐字稿已儲存: {srt_path}")
            
            # 延遲清理片段
            for seg in segments:
                try: os.remove(os.path.join(DOWNLOAD_DIR, seg))
                except: pass
        else:
            print(f"✍️ 正在進行 AI 語音轉譯 (Whisper)...")
            srt_content = transcribe_audio_to_srt(audio_path)
            if "Error" in srt_content:
                print(f"❌ 轉譯失敗: {srt_content}")
                return
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            print(f"✅ 逐字稿已儲存: {srt_path}")
    else:
        print(f"ℹ️ 逐字稿已存在，跳過轉譯。")

    strategy_suffix = "_strategy.txt" if model_name == "gpt-4o" else f"_strategy_{model_name}.txt"
    strategy_path = os.path.join(SOURCE_DIR, f"{base_name}{strategy_suffix}")
    if not os.path.exists(strategy_path):
        print(f"🧠 正在產生 SoR 策略文案 ({model_name})...")
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        transcript_clean = clean_srt_to_text(srt_content)
        strategy_content = generate_sor_content(base_name, transcript_clean, model_name=model_name)
        with open(strategy_path, 'w', encoding='utf-8') as f:
            f.write(strategy_content)
        print(f"✅ 策略文案已儲存: {strategy_path}")
    else:
        print(f"ℹ️ 策略文案已存在，跳過生成。")
    print(f"🎊 影片 '{base_name}' 處理完成！")

def main():
    parser = argparse.ArgumentParser(description="蕭博士 SoR 本地影片處理工具")
    parser.add_argument("path", help="影片檔案路徑或目錄路徑")
    parser.add_argument("--model", default="gemini", help="使用的 AI 模型 (gpt-4o/gemini)")
    args = parser.parse_args()

    if os.path.isfile(args.path):
        process_local_video(args.path, model_name=args.model)
    elif os.path.isdir(args.path):
        exts = ('.mp4', '.mov', '.m4v', '.mkv')
        files = sorted([os.path.join(args.path, f) for f in os.listdir(args.path) if f.lower().endswith(exts)])
        print(f"📂 發現 {len(files)} 個影片檔案。")
        for i, f in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] ---")
            process_local_video(f, model_name=args.model)
    else:
        print(f"❌ 無效的路徑: {args.path}")

if __name__ == "__main__":
    main()
