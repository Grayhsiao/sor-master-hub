"""
Global_Skills / youtube_downloader
=====================================
功能：從 YouTube 網址（單支影片或播放清單）解析影片資訊並下載為 MP3。

用法：
    from Global_Skills.youtube_downloader.youtube_downloader import get_playlist_info, download_audio

    videos, title = get_playlist_info("https://www.youtube.com/playlist?list=PL...")
    for v in videos:
        path = download_audio(v, output_dir="downloaded_files", concept_number=1)

需求：
    pip install yt-dlp
"""

import os
import re
import yt_dlp

# ─── 工具函式 ─────────────────────────────────────

def sanitize_filename(name: str) -> str:
    """移除檔名中的非法字元"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


# ─── 主要函式 ─────────────────────────────────────

def get_playlist_info(url: str) -> tuple[list[dict], str]:
    """
    解析 YouTube 網址（播放清單或單支影片），取得影片清單。

    參數：
        url : YouTube 網址（支援 playlist URL 或單支 watch URL）

    回傳：
        (video_list, playlist_title)
        video_list : [{"id": str, "title": str}, ...]
        playlist_title : 播放清單名稱（單支影片時為影片標題）
    """
    print(f"🔍 正在分析網址...")

    # 如果是帶 list= 的網址，轉換成純播放清單格式以確保抓完整清單
    list_id_match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    target_url = (
        f"https://www.youtube.com/playlist?list={list_id_match.group(1)}"
        if list_id_match else url
    )

    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

    video_list = []
    playlist_title = "未命名系列"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(target_url, download=False)

            if result and "entries" in result:
                # 播放清單
                playlist_title = result.get("title", "未命名系列")
                for entry in result["entries"]:
                    if entry:
                        video_list.append({
                            "id": entry["id"],
                            "title": entry.get("title", "無標題")
                        })
            elif result:
                # 單支影片
                playlist_title = result.get("title", "未命名系列")
                video_list.append({
                    "id": result["id"],
                    "title": result.get("title", "無標題")
                })

    except Exception as e:
        print(f"❌ 解析失敗：{e}")

    print(f"   📊 找到 {len(video_list)} 支影片")
    return video_list, playlist_title


def download_audio(
    video_info: dict,
    output_dir: str = "downloaded_files",
    concept_number: int = 1,
    series_name: str = "",
    skip: bool = False,
    bitrate: str = "64k",
) -> str | None:
    """
    下載指定影片的音訊為 MP3。

    參數：
        video_info      : {"id": str, "title": str}（來自 get_playlist_info）
        output_dir      : 輸出資料夾路徑
        concept_number  : 觀念序號（用於命名，如 01, 02）
        series_name     : 系列名稱（可選，用於命名前綴）
        skip            : 若為 True 則跳過此影片（直接回傳 "SKIPPED"）
        bitrate         : MP3 位元率，預設 "64k"

    回傳：
        下載後的 .mp3 路徑，跳過回傳 "SKIPPED"，失敗回傳 None
    """
    if skip:
        print(f"   ⏭️  跳過（skip=True）：{video_info['title']}")
        return "SKIPPED"

    os.makedirs(output_dir, exist_ok=True)

    safe_title = sanitize_filename(video_info["title"])
    series_prefix = f"[{sanitize_filename(series_name)}]" if series_name else ""
    base_name = f"{series_prefix}觀念{concept_number:02d}_{safe_title}"
    output_path = os.path.join(output_dir, base_name)
    expected_mp3 = f"{output_path}.mp3"

    # 已存在則直接回傳
    if os.path.exists(expected_mp3):
        print(f"   📂 已有 MP3，跳過下載：{os.path.basename(expected_mp3)}")
        return expected_mp3

    url = f"https://www.youtube.com/watch?v={video_info['id']}"
    print(f"   ⬇️  下載中：{safe_title}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate.replace("k", ""),
        }],
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"   ✅ 下載完成：{os.path.basename(expected_mp3)}")
        return expected_mp3
    except Exception as e:
        print(f"   ❌ 下載失敗：{e}")
        return None
