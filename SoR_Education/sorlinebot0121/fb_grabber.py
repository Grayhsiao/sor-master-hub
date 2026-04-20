import os
import re
from facebook_scraper import get_posts
from openai import OpenAI

# ==========================================
# 設定區
# ==========================================
OPENAI_API_KEY = '您的_API_KEY_請填入'
FANPAGE_ID = 'dr.xiao.english' # 目標粉專 ID
PAGES_TO_SCRAPE = 3 
OUTPUT_FILE = "fb.txt" # ★★★ 修改：存到獨立檔案，不汙染主資料庫 ★★★

client = OpenAI(api_key=OPENAI_API_KEY)

def save_to_file(content):
    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write("\n\n" + content + "\n")
        return True
    except: return False

def rewrite_post(original_text):
    print("   ...GPT-4o 正在改寫 FB 貼文...")
    prompt = f"""
    你是【蕭博士】的文案助手。請將這篇 FB 貼文改寫成適合 LINE OA 的短文案。
    【原始貼文】：
    {original_text[:2000]}
    
    【改寫要求】：
    1. 標題格式：🌟 【FB 精選】(自訂標題)
    2. 保留核心觀念，但縮減篇幅，適合 LINE 手機閱讀。
    3. 結尾加上 CTA (👉 ...)。
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except: return None

print(f"🚀 開始抓取粉專【{FANPAGE_ID}】的貼文，並存入 {OUTPUT_FILE}...")

try:
    # cookies='cookies.txt' 為選填，若有檔案可提升穩定度
    posts = get_posts(FANPAGE_ID, pages=PAGES_TO_SCRAPE, cookies='cookies.txt')
    
    count = 0
    for post in posts:
        text = post.get('text')
        post_id = post.get('post_id')
        
        if text and len(text) > 50: # 過濾短文
            print(f"\n📄 發現貼文 (ID: {post_id})...")
            
            # 防呆：檢查 fb.txt 是否已有此文
            is_exist = False
            if os.path.exists(OUTPUT_FILE):
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    if text[:20] in f.read():
                        is_exist = True
            
            if is_exist:
                print("   ⚠️ 已存在，跳過。")
                continue
                
            new_content = rewrite_post(text)
            if new_content:
                save_to_file(new_content)
                print(f"   ✅ 已存入 {OUTPUT_FILE}")
                count += 1
                
    print(f"\n🎉 任務完成！共新增 {count} 篇貼文到 {OUTPUT_FILE}。")
    print("💡 請記得檢查內容後，再手動複製到 database.txt")

except Exception as e:
    print(f"❌ 抓取失敗: {e}")
    print("提示：若失敗請檢查 facebook-scraper 版本或 cookies.txt")