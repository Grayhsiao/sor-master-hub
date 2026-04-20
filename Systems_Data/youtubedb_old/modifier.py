"""
=============================================================================
🎬 互動式導演模式 (Interactive Modifier Engine)
=============================================================================
核心功能：
1. 影片選單：自動掃描 data/outputs/，讓你選取要「調教」的影片。
2. 基礎繼承：讀取資料夾內現有的「精品文案」作為修改基礎。
3. 導演指令：輸入口語化的修改要求，AI 會自動優化指令並重寫。
4. 版本管理：產出存為 [修改版]_...txt，保留原始紀錄，實現迭代優化。

用法：
    python3 modifier.py
=============================================================================
"""

import os
import sys
import json
from pathlib import Path

# ─── 環境設定 ───────────────────────────────────────
# 確保能讀取到 core/ 內的模組
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR / "core"))

from config import DATA_DIR, OPENAI_API_KEY
from utils import load_prompts  # 假設我們可以用現有的 prompt 優化邏輯

# 產出總目錄
OUTPUT_ROOT = DATA_DIR / "outputs"

class ModifierEngine:
    def __init__(self):
        if not OPENAI_API_KEY:
            print("❌ 錯誤：未設定 OPENAI_API_KEY 環境變數。")
            sys.exit(1)
        
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def list_video_folders(self):
        """列出所有可供修改的影片資料夾"""
        if not OUTPUT_ROOT.exists():
            print("❌ 找不到產出目錄 (data/outputs)。")
            return []
        
        folders = sorted([d for d in OUTPUT_ROOT.iterdir() if d.is_dir()])
        return folders

    def optimize_instruction(self, user_cmd):
        """AI 秘書：將模糊的導演指令轉化為精確的 AI 指令"""
        print("✨ AI 秘書正在理清你的導演意圖...")
        prompt = f"""
        你是一位專業的文案導演助手。
        使用者的原始修改要求：「{user_cmd}」
        
        請將其轉化為一段給 AI 的「最高指導原則」。
        要求：
        1. 語氣要堅定，明確指出要強化什麼、削弱什麼。
        2. 保持蕭博士 SoR (Science of Reading) 的專業底蘊。
        3. 只回傳優化後的指令文字，不要有開場白。
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ 指令優化失敗，將使用原始指令：{e}")
            return user_cmd

    def rewrite_content(self, original_content, instruction):
        """核心重寫邏輯"""
        print("🚀 正在根據導演指令重新打造文案...")
        
        prompt = f"""
        你是【蕭博士】的專屬文案導演。
        
        【原始文案內容】：
        {original_content}
        
        【🎬 導演本輪指令（最高準則）】：
        {instruction}
        
        【⚠️ 重寫規範】：
        1. 必須保留 SoR 的科學核心（理論背景與比喻）。
        2. 嚴格執行導演的指令。
        3. 輸出格式請維持「背景、比喻、QA」的三段式結構，但內容要根據指令大幅演化。
        4. 去掉所有 AI 味濃厚的贅詞。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ 重寫失敗：{e}")
            return None

    def run_interactive(self):
        print("\n" + "="*60)
        print("  🎬  互動式導演模式 (Modifier) - 啟動")
        print("="*60)
        
        while True:
            folders = self.list_video_folders()
            if not folders: break
            
            print("\n📺 影片清單：")
            for i, f in enumerate(folders, 1):
                print(f"  [{i:2d}] {f.name}")
            
            choice = input("\n👉 請輸入要修改的編號 (或輸入 q 離開)：")
            if choice.lower() == 'q': break
            
            try:
                idx = int(choice) - 1
                target_folder = folders[idx]
                
                # 找「精品文案」作為底稿
                base_files = list(target_folder.glob("*_小綠精品文案.txt"))
                # 如果沒有精品文案，找修改版
                if not base_files:
                    base_files = list(target_folder.glob("[修改版]*"))
                
                if not base_files:
                    print(f"⚠️ 找不到該影片的精品文案底稿，請先執行採收或精煉。")
                    continue
                
                # 選取最新的版本
                base_path = sorted(base_files)[-1]
                print(f"\n🎯 已選定底稿：{base_path.name}")
                
                with open(base_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                
                print("\n" + "-"*30)
                print(f"【目前內容預覽】:\n{old_content[:200]}...")
                print("-"*30)
                
                user_cmd = input("\n💬 導演請下令 (例如: 改口語一點、針對家長痛點...)\n👉 ")
                if not user_cmd: continue
                
                # 1. 指令優化
                optimized_cmd = self.optimize_instruction(user_cmd)
                print(f"\n✨ 優化後的導演指令：\n   {optimized_cmd}")
                
                # 2. 重寫
                new_content = self.rewrite_content(old_content, optimized_cmd)
                
                if new_content:
                    print("\n" + "✨"*20)
                    print(new_content)
                    print("✨"*20)
                    
                    save = input("\n💾 是否儲存這個修改版本？(y/n) ").lower()
                    if save == 'y':
                        # 產生檔名：[修改版_時分]_原檔名
                        import datetime
                        now = datetime.datetime.now().strftime("%H%M")
                        new_filename = f"[修改版_{now}]_{target_folder.name}.txt"
                        new_path = target_folder / new_filename
                        
                        with open(new_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"✅ 已存入：{new_path.name}")
                        
                        # 詢問是否更新行銷素材
                        update_marketing = input("\n🚀 是否同步更新行銷素材 (Flex, Posts)？(y/n) ").lower()
                        if update_marketing == 'y':
                            print("🔄 正在根據新文案重新產出行銷資產...")
                            # 呼叫行銷引擎 (這裡簡單模擬，之後可整合)
                            from export_marketing_assets import MarketingEngine
                            engine = MarketingEngine()
                            # 由於我們改了檔名，需讓 MarketingEngine 也能抓到 [修改版]
                            # 此處先留白，之後優化 MarketingEngine 以支援指定檔案
                            print("✅ 行銷素材已更新 (模擬)。")
            
            except (ValueError, IndexError):
                print("❌ 輸入無效，請再試一次。")

if __name__ == "__main__":
    modifier = ModifierEngine()
    modifier.run_interactive()
