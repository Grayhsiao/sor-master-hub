"""
=============================================================================
📢 行銷資產自動化加工廠 (Marketing Assets Engine)
=============================================================================
核心功能：
1. 影片核心 (Video-Centric)：自動掃描 data/outputs/ 下的影片專屬資料夾。
2. 深度解析：從「小綠精品文案」中精準提取比喻、理論背景與實戰 QA。
3. 資產歸位：產出的 Line Flex JSON 與社群貼文直接存入該影片資料夾中。
4. 網頁預覽：自動更新 reports/index.html，加入行銷素材預覽連結。

說明文件：docs/SCRIPTS_MANUAL.md
=============================================================================
"""

import os
import re
import json
from pathlib import Path
from config import BASE_DIR, DATA_DIR, INDEX_FILE

# 產出總目錄
OUTPUT_ROOT = DATA_DIR / "outputs"
REPORT_DIR = BASE_DIR / "reports"

class MarketingEngine:
    def __init__(self):
        if not INDEX_FILE.exists():
            print("⚠️ 索引檔案不存在，將使用資料夾名稱作為標題。")
            self.video_map = {}
        else:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                self.video_map = json.load(f)
            
        if not OUTPUT_ROOT.exists():
            print("❌ 找不到產出目錄 (data/outputs)，請先執行採收腳本。")
            return

    def parse_strategy(self, content):
        """解析三段式 SoR 策略文案內容"""
        # 使用正規表達式抓取區塊 (相容 v2.0 SOP)
        background = re.search(r"【理論背景（科學靈魂）】(.*?)(?=【|$)", content, re.S)
        metaphor = re.search(r"【優化觀念（比喻外殼）】(.*?)(?=【|$)", content, re.S)
        qa = re.search(r"【實戰 Q&A】(.*?)$", content, re.S)
        
        return {
            "background": background.group(1).strip() if background else "未提供理論背景",
            "metaphor": metaphor.group(1).strip() if metaphor else "未提供比喻核心",
            "qa": qa.group(1).strip() if qa else "未提供 QA"
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
            "type": "box", "layout": "vertical",
            "contents": [
              { "type": "text", "text": "蕭博士 SoR 每日心法", "weight": "bold", "color": "#1DB446", "size": "sm" },
              { "type": "text", "text": title[:40], "weight": "bold", "size": "xl", "margin": "md", "wrap": True },
              {
                "type": "box", "layout": "vertical", "margin": "lg", "spacing": "sm",
                "contents": [
                  {
                    "type": "box", "layout": "baseline", "spacing": "sm",
                    "contents": [
                      { "type": "text", "text": "💡", "color": "#aaaaaa", "size": "sm", "flex": 1 },
                      { "type": "text", "text": metaphor[:100] + "...", "wrap": True, "color": "#666666", "size": "sm", "flex": 5 }
                    ]
                  }
                ]
              }
            ]
          },
          "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
              {
                "type": "button", "style": "primary", "height": "sm", "color": "#1DB446",
                "action": { "type": "uri", "label": "📺 立即觀看教學", "uri": f"https://youtu.be/{video_id}" }
              }
            ],
            "flex": 0
          }
        }
        return flex

    def process_all_folders(self):
        """遍歷所有影片資料夾並生成行銷資產"""
        if not OUTPUT_ROOT.exists(): return
        
        video_folders = [d for d in OUTPUT_ROOT.iterdir() if d.is_dir()]
        print(f"🚀 開始加工行銷素材，共發現 {len(video_folders)} 個影片資料夾...")

        processed_count = 0
        for folder in video_folders:
            title = folder.name
            # 尋找小綠精品文案
            strategy_file = list(folder.glob("*_小綠精品文案.txt"))
            if not strategy_file:
                print(f"⚠️ 跳過 {title}: 找不到精品文案。")
                continue
                
            strategy_path = strategy_file[0]
            with open(strategy_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 取得 Video ID (從索引或檔案名)
            # 假設 SRT 檔名為 [標題].srt
            srt_file = folder / f"{title}.srt"
            video_id = self.video_map.get(f"{title}.srt", "unknown")
            
            data = self.parse_strategy(content)

            # 1. 生成 LineOA 貼文文字
            line_post = f"🌟 【蕭博士 SoR 每日英語心法】 🌟\n\n📺 影片：https://youtu.be/{video_id}\n\n💡 核心觀念：\n{data['metaphor']}\n\n🧠 腦科學：\n{data['background'][:150]}...\n\n#蕭博士 #SoR #美語教學"
            with open(folder / "marketing_lineoa_post.txt", 'w', encoding='utf-8') as f:
                f.write(line_post)

            # 2. 生成 Threads 貼文
            threads_post = f"🎓 蕭博士 SoR 跳開英文苦海！\n\n「{data['metaphor'][:100]}...」\n\n完整教學 👉 https://youtu.be/{video_id}\n\n#SoR #蕭博士 #英文學習"
            with open(folder / "marketing_threads_post.txt", 'w', encoding='utf-8') as f:
                f.write(threads_post)

            # 3. 生成 Line Flex Message JSON
            if video_id != "unknown":
                flex_json = self.generate_line_flex(video_id, title, data['metaphor'])
                with open(folder / "marketing_line_flex.json", 'w', encoding='utf-8') as f:
                    json.dump(flex_json, f, ensure_ascii=False, indent=2)

            processed_count += 1
            print(f"✅ 已完成: {title}")

        print(f"\n✨ 行銷加工完成！共處理 {processed_count} 個項目。")
        self._update_web_index()

    def _update_web_index(self):
        """強化網頁索引，加入行銷預覽連結"""
        html_path = REPORT_DIR / "index.html"
        if not html_path.exists(): return
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 簡單判斷是否已經有行銷列，沒有的話補上
        if "<th>行銷素材</th>" not in content:
            content = content.replace("<th>原始連結</th>", "<th>原始連結</th><th>行銷素材</th>")
            
        # 對每一行增加預覽按鈕
        # 尋找 data/outputs/標題
        folders = [d.name for d in OUTPUT_ROOT.iterdir() if d.is_dir()]
        for title in folders:
            folder_link = f"../data/outputs/{title}"
            # 在該列末尾補上連結 (簡單字串替換)
            marketing_links = f"<td><a href='{folder_link}/marketing_line_flex.json'>Flex</a> | <a href='{folder_link}/marketing_lineoa_post.txt'>Post</a></td>"
            # 這裡需要更精密的正則，但我們先用簡單的
            pattern = f"<td><a href='../data/outputs/{title}'>📂 查看檔案夾</a></td>"
            replacement = f"{pattern}{marketing_links}"
            if marketing_links not in content:
                content = content.replace(pattern, replacement)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"🔗 網頁索引預覽連結已更新。")

if __name__ == "__main__":
    engine = MarketingEngine()
    engine.process_all_folders()

