"""
=============================================================================
✂️ AI 智慧剪輯刀 Engine (Smart Cutter 3.0)
=============================================================================
核心功能：
1. 自動導航：偵測影片資料夾內的 MP4 或 MP3 資源。
2. 字幕對齊：使用 SRT 精準時間碼，避免切在字中間。
3. 智能緩衝：自動增減時間，讓聲音與畫面聽覺更自然。
4. RAG 整合：提供接口供搜尋頁面直接調用「一鍵剪輯」。
=============================================================================
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import Optional

# 確保能讀取到 core 內的 config
try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class SmartCutterEngine:
    def __init__(self, api_key: Optional[str] = OPENAI_API_KEY):
        if not api_key:
            from config import OPENAI_API_KEY
            api_key = OPENAI_API_KEY
        
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    def parse_srt(self, srt_path: Path):
        """解析 SRT 檔案"""
        if not srt_path.exists():
            return []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
        matches = pattern.findall(content)
        return [{"id": int(m[0]), "start": m[1], "end": m[2], "text": m[3].strip()} for m in matches]

    def time_to_sec(self, t_str):
        if isinstance(t_str, (int, float)): return t_str
        h, m, s = t_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

    def cut(self, video_folder: Path, start_time: str, end_time: str, output_name: str, padding: float = 0.3):
        """
        執行切割任務
        video_folder: 影片專屬資料夾 (data/outputs/標題/)
        start_time, end_time: SRT 格式時間碼 (或秒數)
        output_name: 產出的檔案名稱 (例如: 精華_PA解釋)
        """
        # 1. 尋找來源檔案 (優先順序: MP4 > MP3)
        mp4s = list(video_folder.glob("*.mp4"))
        mp3s = list(video_folder.glob("*.mp3"))
        
        source_file = None
        is_video = False
        
        if mp4s:
            source_file = mp4s[0]
            is_video = True
        elif mp3s:
            source_file = mp3s[0]
            is_video = False
        else:
            return {"status": "error", "message": "資料夾內找不到影片或音訊檔"}

        # 2. 準備輸出路徑
        ext = ".mp4" if is_video else ".mp3"
        output_path = video_folder / f"{output_name}{ext}"
        
        # 3. 計算時間 (加上緩衝)
        s_sec = max(0.0, self.time_to_sec(start_time) - padding)
        e_sec = self.time_to_sec(end_time) + padding
        duration = e_sec - s_sec

        print(f"🔪 正在切割 {'影片' if is_video else '音訊'}: {source_file.name}")
        print(f"⏱️ 時間段: {s_sec} -> {e_sec} (長度: {duration:.2f}s)")

        # 4. 呼叫 FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(s_sec),
            "-t", str(duration),
            "-i", str(source_file),
            "-c:v", "libx264" if is_video else "copy",
            "-c:a", "aac" if is_video else "libmp3lame",
            "-strict", "experimental",
            str(output_path)
        ]
        
        if not is_video:
            # 音訊模式簡化參數
            cmd = ["ffmpeg", "-y", "-ss", str(s_sec), "-t", str(duration), "-i", str(source_file), "-acodec", "copy", str(output_path)]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {
                "status": "success",
                "file": output_path.name,
                "path": str(output_path),
                "is_video": is_video
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ai_smart_select(self, srt_data, query):
        """(選用) 讓 AI 根據問題選出最適合的 SRT ID 範圍 - 繼承自 V2"""
        # 為了簡潔，此處保持原本 V2 的 logic ... (略，如有需要可補回)
        pass

# 直接執行時的簡易測試
if __name__ == "__main__":
    # 測試腳本
    print("🎬 Smart Cutter Engine 測試模式")
    # engine = SmartCutterEngine()
    # ...