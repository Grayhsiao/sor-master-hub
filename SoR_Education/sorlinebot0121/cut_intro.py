import os

# ==========================================
# 📋 設定區
# ==========================================
DOWNLOAD_DIR = "downloaded_files"
TARGET_KEYWORD = "第42堂"
CUT_MINUTES = 6  # 設定要切掉的分鐘數 (前 11 分鐘)
TOTAL_MINUTES = 126 # 影片總長度

# ==========================================
# 核心功能
# ==========================================
print(f"🚀 啟動「前 {CUT_MINUTES} 分鐘切除手術」...")

txt_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".txt") and TARGET_KEYWORD in f]

if txt_files:
    file_path = os.path.join(DOWNLOAD_DIR, txt_files[0])
    
    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()
    
    total_chars = len(full_content)
    print(f"📄 原始檔案字數：{total_chars}")
    
    # 計算切除點
    # 公式：(欲切除時間 / 總時間) * 總字數
    cut_ratio = CUT_MINUTES / TOTAL_MINUTES
    cut_index = int(total_chars * cut_ratio)
    
    # 為了保險，我們往後多切一點點，或者往前保留一點點？
    # 建議：直接切下去，通常音樂雜訊字數比較少，所以這個算法其實會切到「正文開始」的地方。
    # 但因為 Whisper 對音樂有時候會留白，有時候會亂寫，我們採取「關鍵字輔助定位」更保險。
    
    print(f"📊 依時間比例推算，應切除前 {cut_index} 個字。")
    print(f"👀 讓我們看看切除點附近的文字：\n")
    print(f"--- 切除點前 50 字 ---\n{full_content[cut_index-50:cut_index]}")
    print(f"\n--- 切除點後 100 字 (這將是新的開頭) ---\n{full_content[cut_index:cut_index+100]}")
    print("-" * 50)
    
    confirm = input("👉 確認要從這裡切斷並儲存嗎？(y/n): ").lower()
    
    if confirm == 'y':
        new_content = full_content[cut_index:]
        # 覆蓋存檔，或另存新檔？建議另存，比較安全。
        new_filename = file_path.replace(".txt", "_clean.txt")
        
        with open(new_filename, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"\n✅ 手術成功！")
        print(f"📂 已儲存乾淨檔案：{os.path.basename(new_filename)}")
        print("💡 接下來請用這份 '_clean.txt' 檔案來跑分析程式。")
        
    else:
        print("🚫 取消操作。")

else:
    print(f"❌ 找不到檔案！")