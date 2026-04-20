import re
import os

def process_fb_data(input_file, output_dir="knowledge_base", filtered_dir="filtered_posts", word_count_threshold=200):
    """
    處理 Facebook 貼文資料
    1. 依據分隔線拆分
    2. 過濾短文 (留言/雜訊) -> 存入 filtered_dir
    3. 自動加上 🌟 與標題
    4. 存入指定資料夾
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 已建立匯入資料夾: {output_dir}")
        
    if not os.path.exists(filtered_dir):
        os.makedirs(filtered_dir)
        print(f"📁 已建立過濾資料夾: {filtered_dir}")

    if not os.path.exists(input_file):
        print(f"找不到檔案: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # 依據分隔線拆分貼文
    posts = re.split(r'={20,}', raw_content)
    
    valid_count = 0
    skipped_count = 0

    for i, post in enumerate(posts):
        post = post.strip()
        if not post:
            continue

        # 提取編號與內容
        try:
            # 修正：提取真正的「編號」而非「字數」
            id_match = re.search(r'【編號】：(\d+)', post)
            id_val = id_match.group(1) if id_match else i
            
            # 提取字數標籤的值
            wc_match = re.search(r'【字數】：(\d+)', post)
            word_count = int(wc_match.group(1)) if wc_match else 0
            
            # 提取內容後面的所有文字
            content_match = re.search(r'【內容】：\n(.*)', post, re.DOTALL)
            if not content_match:
                continue
            
            content = content_match.group(1).strip()
            
            # --- 規則過濾 ---
            filename_base = f"{int(id_val):03d}" if str(id_val).isdigit() else f"{id_val}"
            
            # 判斷是否為「正式貼文」(通常有 【標題】)
            has_title = re.search(r'【.*?】', content)
            
            # 1. 鐵律：社交禮儀過濾 (留言條件)
            social_etiquette = ["謝謝分享", "老師好", "感恩老師", "收穫滿滿", "辛苦了", "期待下一堂", "推一個"]
            subjective_emotions = ["這真的太棒了", "很有感", "受教了", "認同", "👍", "❤️"]
            
            # --- 判定為「留言」的特徵 (鐵律準則) ---
            # A. 純粹社交禮儀 或 B. 短暫情感抒發 (通常伴隨 FB 介面雜訊)
            is_etiquette = any(kw in content for kw in social_etiquette)
            is_emotion = word_count < 30 and any(kw in content for kw in subjective_emotions)
            
            # C. FB 介面雜訊 (關鍵判定留言的鐵證)
            noise_keywords = ["讚\n回覆", "週\n讚", "讚\n留言\n分享", "查看貼文", "所有心情：", "尚無留言"]
            is_noise_metadata = any(kw in content for kw in noise_keywords)
            
            if is_noise_metadata or is_etiquette or is_emotion:
                # 只有當它「完全沒有正文標題格式」時才當作留言剔除
                if not has_title:
                    with open(os.path.join(filtered_dir, f"filtered_{filename_base}.txt"), 'w', encoding='utf-8') as ff:
                        reason = "社交禮儀/留言特徵" if is_etiquette or is_emotion else "FB介面雜訊"
                        ff.write(f"(鐵律判定為留言: {reason})\n\n{content}")
                    skipped_count += 1
                    continue
            
            # 2. 鐵律：獨立邏輯與篇幅判斷 (貼文條件)
            # A. 篇幅 > 50 且 無雜訊關鍵字
            # B. 具有明確主題 (標題)
            is_short_and_untitled = word_count < 50 and not has_title
            
            if is_short_and_untitled:
                with open(os.path.join(filtered_dir, f"filtered_{filename_base}.txt"), 'w', encoding='utf-8') as ff:
                    ff.write(f"(鐵律判定為留言: 篇幅不足且無獨立標題, 字數: {word_count})\n\n{content}")
                skipped_count += 1
                continue

            # --- 自動美化與標註 ---
            # 統一加上 🌟
            final_content = f"🌟 {content}"

            # 儲存檔案
            # 優化：檔名包含原始編號以方便排序
            filename = f"fb_post_{filename_base}.txt"
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            valid_count += 1

        except Exception as e:
            print(f"處理第 {i} 篇時出錯: {e}")

    print(f"--- 處理完成 ---")
    print(f"成功匯入: {valid_count} 篇")
    print(f"過濾雜訊: {skipped_count} 篇 (留言或短文)")
    print(f"檔案已存至: {output_dir}")

if __name__ == "__main__":
    # 使用者執行時請將檔名改為您的原始檔名
    process_fb_data("all_posts.txt")
