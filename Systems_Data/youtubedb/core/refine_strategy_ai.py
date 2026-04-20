import os
import glob
import time
import argparse
import re
from config import SOURCE_DIR
from utils import clean_srt_to_text, generate_sor_content

def generate_and_save_strategy(srt_path, model_name="gpt-4o", current=1, total=1):
    """Processes a single SRT/TXT file and saves the strategy to a new file."""
    filename = os.path.basename(srt_path)
    # Remove extension .srt or .txt
    title = re.sub(r'\.(srt|txt)$', '', filename, flags=re.IGNORECASE)
    
    if "_" in title:
        title_display = title.split("_", 1)[1]
    else:
        title_display = title
    
    prefix = f"[{current}/{total}][{model_name}]"
    print(f"\n{prefix} === Processing: {title_display} ===")
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # clean_srt_to_text works for plain text too (it just won't find candidates to remove)
        transcript = clean_srt_to_text(content)
        content_ai = generate_sor_content(title_display, transcript, model_name=model_name)
        
        suffix = "_strategy.txt" if model_name == "gpt-4o" else f"_strategy_{model_name}.txt"
        output_path = os.path.join(SOURCE_DIR, title + suffix)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content_ai)
            
        print(f"{prefix} ✅ Done! Saved to: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"{prefix} ❌ Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="SRT/TXT Reprocessing Tool (SoR SOP 2.0 Optimized)")
    parser.add_argument("target", nargs="?", help="Index (number) or keyword/filename to process. If omitted, processes all.")
    parser.add_argument("--list", action="store_true", help="List all available files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing strategy files.")
    parser.add_argument("--model", default="gpt-4o", choices=["gpt-4o", "gemini"], help="Select AI model")
    parser.add_argument("--compare", action="store_true", help="Process each file with BOTH models.")
    
    args = parser.parse_args()
    
    # Scan for both .srt and .txt
    src_files = []
    for ext in ["*.srt", "*.txt"]:
        src_files.extend(glob.glob(os.path.join(SOURCE_DIR, ext)))
    src_files = sorted(src_files)
    
    if args.list:
        for i, f_path in enumerate(src_files, 1):
            base_name = re.sub(r'\.(srt|txt)$', '', os.path.basename(f_path), flags=re.IGNORECASE)
            gpt_exists = " ✅ GPT" if os.path.exists(os.path.join(SOURCE_DIR, base_name + "_strategy.txt")) else ""
            gemini_exists = " ✅ GEM" if os.path.exists(os.path.join(SOURCE_DIR, base_name + "_strategy_gemini.txt")) else ""
            print(f"[{i:02d}] {os.path.basename(f_path)}{gpt_exists}{gemini_exists}")
        return

    targets = []
    if args.target:
        if args.target.isdigit():
            idx = int(args.target) - 1
            if 0 <= idx < len(src_files): targets = [src_files[idx]]
        else:
            targets = [f for f in src_files if args.target.lower() in os.path.basename(f).lower()]
    else:
        targets = src_files

    if not targets:
        print(f"\n❌ 找不到符合 '{args.target}' 的檔案。")
        print(f"請確認檔案是否已放入 `data/sources/` 資料夾中。")
        print(f"目前的檔案清單如下：")
        for i, f_path in enumerate(src_files, 1):
            print(f"  [{i}] {os.path.basename(f_path)}")
        return

    for i, srt_path in enumerate(targets, 1):
        if args.compare:
            generate_and_save_strategy(srt_path, model_name="gpt-4o", current=i, total=len(targets))
            generate_and_save_strategy(srt_path, model_name="gemini", current=i, total=len(targets))
        else:
            generate_and_save_strategy(srt_path, model_name=args.model, current=i, total=len(targets))
        time.sleep(0.5)

if __name__ == "__main__":
    main()
