import os
import sys
import shutil
from utils import generate_sor_content
from config import SOURCE_DIR

def import_text(file_path, title=None):
    """將本地文字檔轉化為 SoR 知識點並存入系統"""
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return

    base_name = os.path.basename(file_path)
    if not title:
        title = os.path.splitext(base_name)[0]
    
    # 1. 讀取原始內容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        print("❌ 檔案內容為空，取消匯入。")
        return

    print(f"📄 正在處理文字檔：{title}...")

    # 2. 生成 AI 策略文案
    print("🤖 正在生成 SoR 策略分析...")
    strategy = generate_sor_content(title, content)

    # 3. 準備目標路徑
    # 統一存放在 sources 資料夾，格式為 title.txt 與 title_strategy.txt
    target_txt = os.path.join(SOURCE_DIR, base_name)
    target_strategy = os.path.join(SOURCE_DIR, f"{os.path.splitext(base_name)[0]}_strategy.txt")

    # 4. 寫入檔案
    with open(target_txt, 'w', encoding='utf-8') as f:
        f.write(content)
    with open(target_strategy, 'w', encoding='utf-8') as f:
        f.write(strategy)

    print("-" * 30)
    print(f"✅ 匯入成功！")
    print(f"📁 原始檔已存至: {target_txt}")
    print(f"✨ 策略文案已存至: {target_strategy}")
    print(f"💡 提示：請啟動 app.py 並點擊「重建資料庫」來完成全文檢索索引。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式: python3 import_text_local.py [檔案路徑]")
        sys.exit(1)
    
    path = sys.argv[1]
    import_text(path)
