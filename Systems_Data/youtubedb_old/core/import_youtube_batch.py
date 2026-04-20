"""
=============================================================================
📺 YouTube 影音採收工廠 (YouTube Batch Ingestion)
=============================================================================
核心功能：
1. 批量採收：支援 YouTube 播放清單或單一影片連結。
2. 字幕優先：優先下載 YouTube 內建或自動生成的繁中/英文字幕 (省時省錢)。
3. AI 備援：若無字幕，自動啟動 OpenAI Whisper 進行高精準聽寫。
4. 雙重產出：同時生成「小綠精品版」策略文案與「LineOA 全文版」知識備份。
5. 自動歸檔：依影片標題建立專屬資料夾，存放在 data/outputs/。
6. 網頁索引：自動更新 reports/index.html 索引頁。

說明文件：docs/SCRIPTS_MANUAL.md
=============================================================================
"""

import os
import json
import re
import time
import yt_dlp
import subprocess
import sys
from pathlib import Path
from config import BASE_DIR, DATA_DIR, DOWNLOAD_DIR, INDEX_FILE
from utils import clean_srt_to_text, generate_sor_content, openai_client

# 🎯 目標清單 (可貼上單一影片或播放清單網址)
TARGET_URL = "https://www.youtube.com/watch?v=r7tyCmzZEa8&list=PL68aZEUti9QAlfA1rKmNqZBXL1Yfi6Put&index=1" 

# 產出總目錄
OUTPUT_ROOT = DATA_DIR / "outputs"
REPORT_DIR = BASE_DIR / "reports"

class YouTubeHarvester:
    def __init__(self):
        self.stats = {
            "total": 0,
            "downloaded": 0,
            "transcribed_ai": 0,
            "subtitle_builtin": 0,
            "refined": 0,
            "errors": 0
        }
        self.results = []
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, name):
        """過濾非法字元以免路徑報錯"""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    def get_video_info(self, url):
        """取得影片資訊彙整"""
        print(f"🔍 正在解析網址: {url}")
        ydl_opts = {
            'dump_single_json': True,
            'flat_playlist': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return info
            except Exception as e:
                print(f"❌ 解析失敗: {e}")
                return None

    def process_video(self, video_url):
        """核心處理流程：下載 -> 字幕 -> 文案 -> 歸檔"""
        self.stats["total"] += 1
        print(f"\n🎬 正在處理影片 ({self.stats['total']}): {video_url}")
        
        try:
            # 1. 下載影片與字幕
            info = self._download_assets(video_url)
            if not info:
                self.stats["errors"] += 1
                return

            video_id = info['id']
            title = self.sanitize_filename(info.get('title', video_id))
            
            # 2. 建立專屬資料夾 (data/outputs/標題)
            video_folder = OUTPUT_ROOT / title
            video_folder.mkdir(parents=True, exist_ok=True)
            
            # 3. 尋找或生成字幕 (SRT)
            srt_path, is_ai = self._get_srt(info, video_folder)
            if not srt_path:
                print("❌ 無法取得字幕，跳過此片。")
                self.stats["errors"] += 1
                return
            
            # 讀取全文
            with open(srt_path, 'r', encoding='utf-8') as f:
                raw_srt = f.read()
                transcript_text = clean_srt_to_text(raw_srt)

            # 4. 雙重 AI 文案精煉
            print(f"🧠 正在生成雙重文案...")
            # (A) 小綠精品版
            strategy_content = generate_sor_content(title, transcript_text, template_id="sor_v2_xiao")
            strategy_path = video_folder / f"{title}_小綠精品文案.txt"
            with open(strategy_path, 'w', encoding='utf-8') as f:
                f.write(strategy_content)

            # (B) LineOA 全文版
            line_oa_content = generate_sor_content(title, transcript_text, template_id="line_oa_full_text")
            line_oa_path = video_folder / f"{title}_LineOA全文版.txt"
            with open(line_oa_path, 'w', encoding='utf-8') as f:
                f.write(line_oa_content)

            # 5. 檔案歸位 (也搬移 MP3)
            mp3_source = Path(f"downloads/{video_id}_{title}.mp3")
            if mp3_source.exists():
                mp3_dest = video_folder / f"{title}.mp3"
                mp3_source.rename(mp3_dest)

            # 6. 更新索引
            self._update_index(video_id, title)
            
            # 紀錄結果
            self.stats["refined"] += 1
            if is_ai: self.stats["transcribed_ai"] += 1
            else: self.stats["subtitle_builtin"] += 1
            
            self.results.append({
                "title": title,
                "folder": title, # 相對於 OUTPUT_ROOT
                "url": video_url,
                "id": video_id
            })
            print(f"✅ 完工！檔案存放在: {video_folder}")

        except Exception as e:
            print(f"❌ 處理過程發生錯誤: {e}")
            self.stats["errors"] += 1

    def _download_assets(self, video_url, save_video=False):
        """下載影片/音訊與內建字幕"""
        if save_video:
            # 完整影片模式 (MP4)
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(id)s_%(title)s.%(ext)s',
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['zh-Hant', 'zh-TW', 'zh-Hans', 'zh-CN', 'en'],
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
        else:
            # 僅音訊模式 (MP3)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(id)s_%(title)s.%(ext)s',
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['zh-Hant', 'zh-TW', 'zh-Hans', 'zh-CN', 'en'],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if info: self.stats["downloaded"] += 1
            return info

    def _get_srt(self, info, target_folder):
        """優先找下載的字幕檔案，沒有就呼叫 Whisper"""
        video_id = info['id']
        title = self.sanitize_filename(info.get('title', video_id))
        
        # A. 檢查 yt-dlp 是否下載了字幕 (.srt 或 .vtt)
        # yt-dlp 預設存放在 DOWNLOAD_DIR/
        srt_patterns = [
            DOWNLOAD_DIR / f"{video_id}_{title}.zh-Hant.srt",
            DOWNLOAD_DIR / f"{video_id}_{title}.zh-TW.srt",
            DOWNLOAD_DIR / f"{video_id}_{title}.zh-Hans.srt",
            DOWNLOAD_DIR / f"{video_id}_{title}.en.srt"
        ]
        
        for p in srt_patterns:
            if p.exists():
                # 搬移到目標資料夾
                dest = target_folder / f"{title}.srt"
                p.rename(dest)
                print(f"✨ 發現內建字幕: {p}")
                return dest, False

        # B. 備援：Whisper 聽寫
        print(f"🎙️ 未發現字幕，啟動 AI 聽寫 (Whisper)...")
        mp3_path = DOWNLOAD_DIR / f"{video_id}_{title}.mp3"
        dest_srt = target_folder / f"{title}.srt"
        
        if not mp3_path.exists():
            return None, True

        try:
            with open(mp3_path, "rb") as f:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1", file=f, response_format="srt"
                )
            with open(dest_srt, 'w', encoding='utf-8') as f:
                f.write(transcript)
            return dest_srt, True
        except Exception as e:
            print(f"❌ Whisper 聽寫失敗: {e}")
            return None, True

    def _update_index(self, video_id, title):
        """更新全域索引檔案"""
        data = {}
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                try: data = json.load(f)
                except: data = {}
        
        data[f"{title}.srt"] = video_id
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def generate_report(self):
        """產生結案報告與 HTML 索引連結"""
        print("\n" + "="*50)
        print("📊 影音採收任務報告")
        print("="*50)
        print(f"🔍 掃描影片數: {self.stats['total']}")
        print(f"📥 成功下載數: {self.stats['downloaded']}")
        print(f"✨ 內建字幕數: {self.stats['subtitle_builtin']}")
        print(f"🎙️ AI 聽寫數: {self.stats['transcribed_ai']}")
        print(f"📝 文案加工數: {self.stats['refined']}")
        print(f"❌ 失敗錯誤數: {self.stats['errors']}")
        print("="*50)
        
        html_path = REPORT_DIR / "index.html"
        
        # 讀取現有內容或建立新標題
        existing_rows = ""
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 簡單提取 <tr> 內容
                m = re.findall(r'<tr>(.*?)</tr>', content, re.S)
                if m: existing_rows = "\n".join([f"<tr>{i}</tr>" for i in m[1:]]) # 跳過表頭

        new_rows = ""
        for r in self.results:
            # 連結指向 ../data/outputs/[標題]
            new_rows += f"<tr><td>{r['title']}</td><td><a href='../data/outputs/{r['title']}'>📂 查看檔案夾</a></td><td><a href='https://youtu.be/{r['id']}' target='_blank'>📺 原片</a></td></tr>"
            
        html_content = f"""
        <html><head><meta charset='utf-8'><title>蕭博士內容工廠 - 採收索引</title>
        <style>body{{font-family:sans-serif;padding:20px;}} table{{width:100%;border-collapse:collapse;}} th,td{{padding:10px;border:1px solid #ddd; text-align:left;}} th{{background:#f4f4f4;}}</style>
        </head><body>
        <h1>📺 影音採收索引頁</h1>
        <table><tr><th>影片標題</th><th>產出檔案夾</th><th>原始連結</th></tr>
        {new_rows}
        {existing_rows}
        </table></body></html>
        """
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"🔗 網頁索引頁已更新: {html_path.absolute()}")

def main():
    harvester = YouTubeHarvester()
    info = harvester.get_video_info(TARGET_URL)
    
    if not info: return

    # 判斷是單一影片還是播放清單
    if 'entries' in info:
        print(f"📝 發現播放清單，包含 {len(info['entries'])} 支影片。")
        for entry in info['entries']:
            if entry:
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                harvester.process_video(video_url)
    else:
        harvester.process_video(TARGET_URL)

    harvester.generate_report()

if __name__ == "__main__":
    main()


