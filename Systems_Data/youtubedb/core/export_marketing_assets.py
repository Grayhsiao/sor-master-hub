import os
import re
import json
from config import SOURCE_DIR, INDEX_FILE

class MarketingEngine:
    def __init__(self):
        if not os.path.exists(INDEX_FILE):
            raise FileNotFoundError("INDEX_FILE not found.")
        
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            self.video_map = json.load(f)
            
        self.output_dir = os.path.join(os.path.dirname(SOURCE_DIR), "marketing_assets")
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_strategy(self, content):
        """解析 SoR 策略文案內容"""
        background = re.search(r"【理論背景（科學靈魂）】(.*?)(?=【|$)", content, re.S)
        metaphor = re.search(r"【優化觀念（比喻外殼）】(.*?)(?=【|$)", content, re.S)
        qa = re.search(r"【實戰 Q&A】(.*?)$", content, re.S)
        
        return {
            "background": background.group(1).strip() if background else "",
            "metaphor": metaphor.group(1).strip() if metaphor else "",
            "qa": qa.group(1).strip() if qa else ""
        }

    def generate_line_flex(self, video_id, title, metaphor):
        """產生 Line Flex Message JSON 格式"""
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        flex = {
          "type": "bubble",
          "hero": {
            "type": "image",
            "url": thumbnail,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": {
              "type": "uri",
              "uri": f"https://youtu.be/{video_id}"
            }
          },
          "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "蕭博士 SoR 每日心法",
                "weight": "bold",
                "color": "#1DB446",
                "size": "sm"
              },
              {
                "type": "text",
                "text": title[:40],
                "weight": "bold",
                "size": "xl",
                "margin": "md",
                "wrap": True
              },
              {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": [
                  {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                      {
                        "type": "text",
                        "text": "💡",
                        "color": "#aaaaaa",
                        "size": "sm",
                        "flex": 1
                      },
                      {
                        "type": "text",
                        "text": metaphor[:100] + "...",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                        "flex": 5
                      }
                    ]
                  }
                ]
              }
            ]
          },
          "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
              {
                "type": "button",
                "style": "primary",
                "height": "sm",
                "color": "#1DB446",
                "action": {
                  "type": "uri",
                  "label": "📺 立即觀看教學",
                  "uri": f"https://youtu.be/{video_id}"
                }
              }
            ],
            "flex": 0
          }
        }
        return flex

    def export_all(self):
        strategy_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith("_strategy.txt")]
        
        for filename in strategy_files:
            srt_name = filename.replace("_strategy.txt", ".srt")
            # Also handle potentially generated gemini versions
            if "_gemini" in filename:
                base_name = filename.replace("_strategy_gemini.txt", ".srt")
            else:
                base_name = srt_name

            video_id = self.video_map.get(base_name, "unknown")
            with open(os.path.join(SOURCE_DIR, filename), 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            data = self.parse_strategy(raw_content)
            title = base_name.split("_", 1)[1] if "_" in base_name else base_name
            title = title.replace(".srt", "")

            # 1. LineOA Text
            line_post = f"🌟 【蕭博士 SoR 每日英語心法】 🌟\n\n📺 影片：https://youtu.be/{video_id}\n\n💡 核心觀念：\n{data['metaphor']}\n\n🧠 腦科學：\n{data['background'][:120]}...\n\n#蕭博士 #SoR"
            with open(os.path.join(self.output_dir, f"post_lineoa_{video_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(line_post)

            # 2. Threads/Short
            threads_post = f"🎓 蕭博士 SoR 跳開英文苦海！\n\n「{data['metaphor'][:80]}...」\n\n完整教學 👉 https://youtu.be/{video_id}\n\n#SoR #蕭博士 #英文學習"
            with open(os.path.join(self.output_dir, f"post_threads_{video_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(threads_post)

            # 3. Line Flex JSON
            flex_json = self.generate_line_flex(video_id, title, data['metaphor'])
            with open(os.path.join(self.output_dir, f"flex_lineoa_{video_id}.json"), 'w', encoding='utf-8') as f:
                json.dump(flex_json, f, ensure_ascii=False, indent=2)

            print(f"✅ Generated assets for {video_id} (Text, Threads, Flex JSON)")

if __name__ == "__main__":
    engine = MarketingEngine()
    engine.export_all()
