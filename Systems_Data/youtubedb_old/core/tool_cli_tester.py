import os
import sys
from utils import generate_sor_content

def manual_test():
    print("=== 蕭博士 SoR 內容生成測試工具 ===")
    print("模式：[1] 直接貼上文字 [2] 讀取文字檔")
    choice = input("請選擇模式 (1/2): ").strip()

    title = input("請輸入測試標題 (例如：測試影片01): ").strip() or "測試影片"
    transcript = ""

    if choice == "1":
        print("\n請貼上您的逐字稿內容 (輸入完畢後請在新的一行輸入 'EOF' 或按 Ctrl+D 結束):")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            except EOFError:
                break
        transcript = "\n".join(lines)
    elif choice == "2":
        file_path = input("請輸入文字檔的路徑: ").strip()
        if not os.path.exists(file_path):
            print(f"❌ 找不到檔案：{file_path}")
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
    else:
        print("❌ 無效選擇")
        return

    if not transcript.strip():
        print("❌ 內容為空，取消測試。")
        return

    print(f"\n🤖 正在使用 GPT-4o 生成 SoR 策略文案 (標題: {title})...")
    result = generate_sor_content(title, transcript)
    
    print("\n" + "="*50)
    print("✨ 生成結果：")
    print("="*50)
    print(result)
    print("="*50)
    
    save = input("\n需要將結果儲存為檔案嗎？(y/n): ").strip().lower()
    if save == 'y':
        out_name = f"test_{int(os.path.getmtime(__file__))}.txt"
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"✅ 已儲存至 {out_name}")

if __name__ == "__main__":
    manual_test()
