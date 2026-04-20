import os
import shutil
from datetime import datetime

# --- 設定路徑 ---
# 根據你的截圖，來源路徑約為：/Users/gray/python project/youtubedb/data/sources
# 你可以將此程式放在該目錄下執行，或直接修改下方路徑
source_dir = './'  # 目前所在的資料夾
target_dir = './extracted_txt_files'  # 存放點

def extract_txt_files(src, dst):
    # 如果目標資料夾不存在，就建立一個
    if not os.path.exists(dst):
        os.makedirs(dst)
        print(f"已建立目標資料夾: {dst}")

    count = 0
    # 使用 os.walk 遍歷所有子資料夾
    for root, dirs, files in os.walk(src):
        # 排除掉目標資料夾本身，避免無限循環
        if os.path.abspath(root) == os.path.abspath(dst):
            continue
            
        for file in files:
            if file.endswith('.txt'):
                source_file_path = os.path.join(root, file)
                target_file_path = os.path.join(dst, file)

                # 處理檔名重複的情況（如果不同資料夾有同名檔案，會加上序號）
                base, extension = os.path.splitext(file)
                counter = 1
                while os.path.exists(target_file_path):
                    target_file_path = os.path.join(dst, f"{base}_{counter}{extension}")
                    counter += 1

                shutil.copy2(source_file_path, target_file_path)
                print(f"已拷貝: {file}")
                count += 1

    print(f"\n任務完成！共拷貝了 {count} 個 .txt 檔案到 {dst}")

if __name__ == "__main__":
    extract_txt_files(source_dir, target_dir)