import re
import requests
import core.config as config

class YouTubeAPIManager:
    _cache = {}
    _channel_cache = {}

    @staticmethod
    def extract_video_id(url):
        match = re.search(r'(?:v=|youtu\.be/)([^&?]+)', url)
        return match.group(1) if match else None

    @staticmethod
    def extract_channel_info(url):
        match = re.search(r'youtube\.com/@([^/?&]+)', url)
        if match: return match.group(1), "handle"
        match = re.search(r'youtube\.com/channel/([^/?&]+)', url)
        if match: return match.group(1), "channelId"
        match = re.search(r'youtube\.com/c/([^/?&]+)', url)
        if match: return match.group(1), "username"
        match = re.search(r'youtube\.com/user/([^/?&]+)', url)
        if match: return match.group(1), "username"
        return None, None

    @staticmethod
    def check_video(video_id):
        if video_id in YouTubeAPIManager._cache:
            return YouTubeAPIManager._cache[video_id], "video_cache"
        if not config.YOUTUBE_API_KEY: return "unknown", "no_api_key"
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,topicDetails&id={video_id}&key={config.YOUTUBE_API_KEY}"
        try:
            r = requests.get(url, timeout=1.5)
            data = r.json()
            if not data.get("items"): return "unknown", "api_empty"
            
            item = data["items"][0]
            channel_id = item.get("snippet", {}).get("channelId", "")
            channel_title = item.get("snippet", {}).get("channelTitle", "")
            
            # 優先檢查頻道快取 (還是要等 API 告訴我們頻道 ID)
            if channel_id and channel_id in YouTubeAPIManager._channel_cache:
                return YouTubeAPIManager._channel_cache[channel_id], "channel_cache"

            category_id = item.get("snippet", {}).get("categoryId", "")
            topics = item.get("topicDetails", {}).get("topicCategories", [])
            topics_str = " ".join(topics).lower()
            
            # 娛樂判定 (1: Animation, 20: Gaming, 23: Comedy)
            # 移除了 22(人物) 與 24(娛樂)，讓這些較模糊的分類交給 Gemini 做智慧判定
            if category_id in ["1", "20", "23"] or any(kw in topics_str for kw in ["game", "esports", "animation"]):
                res = "entertainment"
            elif category_id in ["10", "27", "28"]:
                res = "learning"
            else:
                res = "unknown"
            
            YouTubeAPIManager._cache[video_id] = res
            if channel_id and res != "unknown":
                YouTubeAPIManager._channel_cache[channel_id] = res
                
            if res == "entertainment" and channel_title:
                channel_lower = channel_title.lower()
                if channel_lower not in AIClassifier.CLOUD_BLACKLIST:
                    AIClassifier.CLOUD_BLACKLIST.append(channel_lower)

            return res, "youtube_api_fresh"
        except:
            return "unknown"

class AIClassifier:
    CLOUD_BLACKLIST = []

    @staticmethod
    def update_cloud_blacklist(new_list):
        AIClassifier.CLOUD_BLACKLIST.clear()
        AIClassifier.CLOUD_BLACKLIST.extend(new_list)

    @staticmethod
    def classify_content(title, url):
        text = (title + " " + url).lower()
        url_clean = url.split("?")[0].rstrip("/").lower()
        
        # --- 0. 雲端與本地黑名單合併檢查 ---
        full_blacklist = config.HARD_BLACKLIST + AIClassifier.CLOUD_BLACKLIST
        
        # 1. 第一層：關鍵字與 Shorts 阻擋 (最優先！)
        if any(word in text for word in full_blacklist):
            return "entertainment", "blacklist"
            
        if "youtube.com/shorts/" in url.lower():
            return "entertainment", "shorts"

        # 1.5 學習白名單 (次優先：如果沒觸發黑名單，但標題有學科字眼，直接放行)
        if any(word in text for word in config.HARD_WHITELIST):
            return "learning", "whitelist"

        # --- 2. 白名單：允許 YouTube 首頁與搜尋結果 ---
        if url_clean in ["https://www.youtube.com", "https://m.youtube.com", "https://youtube.com"]:
            return "learning", "youtube_home"
        if "/results" in url.lower() and "search_query" in url.lower():
            return "learning", "youtube_search"

        # --- 2.1 快速音樂放行 ---
        if any(kw in text for kw in ["mv", "official audio", "歌", "音樂", "song", "lyrics"]):
            return "learning", "music_keyword"
            
        # 2. 第二層：YouTube 官方 API 精準判定
        if "youtube.com" in url.lower() or "youtu.be" in url.lower():
            vid = YouTubeAPIManager.extract_video_id(url)
            if vid:
                yt_res, yt_reason = YouTubeAPIManager.check_video(vid)
                if yt_res != "unknown": return yt_res, yt_reason
        
        # 3. 第三層：AI 語意判定 (Gemini)
        if not config.GEMINI_API_KEY: return "learning", "no_api_key"
        try:
            payload = {
                "contents": [{"parts": [{"text": f"請判斷此內容是否具有『學術教育價值』或屬於『學科學習』。如果是教育類請回傳 learning，如果是生活娛樂、開箱、Vlog、綜藝或純音樂，請回傳 entertainment。內容：{title} {url}"}]}]
            }
            url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config.GEMINI_API_KEY}"
            r = requests.post(url_api, json=payload, timeout=1.5)
            res = r.json()['candidates'][0]['content']['parts'][0]['text'].strip().lower()
            
            # 嚴格模式：只有明確判定為學習才放行
            if "learning" in res and "entertainment" not in res:
                return "learning", "gemini_ai"
            else:
                return "entertainment", "gemini_ai"
        except:
            # 如果是 YouTube 但 API 失敗，且沒觸發關鍵字，預設較為寬鬆（避免誤殺音樂）
            if "youtube.com" in url.lower(): 
                return "learning", "gemini_fallback"
            return "learning", "gemini_error"
