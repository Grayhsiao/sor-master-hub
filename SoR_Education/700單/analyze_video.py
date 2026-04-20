from moviepy import VideoFileClip
import os

video_path = "last 影片.mp4"
try:
    clip = VideoFileClip(video_path)
    print(f"影片檔名: {video_path}")
    print(f"影片長度: {clip.duration:.2f} 秒")
    print(f"影片解析度: {clip.w}x{clip.h}")
    print(f"影片幀率: {clip.fps} fps")
    
    # 截取中間位置的畫面作為預覽 (如果影片夠長)
    preview_time = min(10, clip.duration / 2)
    preview_filename = "video_preview.jpg"
    clip.save_frame(preview_filename, t=preview_time)
    print(f"已生成預覽圖: {preview_filename}")
    
    clip.close()
except Exception as e:
    print(f"影片分析發生錯誤: {e}")
