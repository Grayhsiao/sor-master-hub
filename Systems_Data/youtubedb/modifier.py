"""
youtubedb/modifier.py
========================
互動式文案修改工具。
從 database.txt 選取一個觀念，找到原始逐字稿，根據你的導演指令重寫文案。

遷移自：sorlinebot0121/modifier.py
升級：使用 Global_Skills 模組取代內嵌函式，使用 .env 避免硬寫 API Key

用法：
    cd youtubedb
    python3 modifier.py
"""

import os
import re
import sys
import glob

# ─── 路徑設定（讓 Global_Skills 可以被 import）───────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from openai import OpenAI
from Global_Skills.audio_transcriber import transcribe_audio
from Global_Skills.common_utils import sanitize_filename, append_to_database

# ─── 設定 ─────────────────────────────────────────
DB_FILE  = os.path.join(os.path.dirname(__file__), "data", "database.txt")
SRC_DIR  = os.path.join(os.path.dirname(__file__), "data", "sources")

def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ 請設定環境變數 OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


# ─── 資料庫 ────────────────────────────────────────

def load_concepts_from_db(db_file: str = DB_FILE) -> list[dict]:
    """從 database.txt 讀取所有觀念標題"""
    if not os.path.exists(db_file):
        print(f"❌ 找不到 {db_file}")
        return []

    with open(db_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    concepts = []
    pattern = r"🌟\s*【(.*?)】(.*)"
    for line in lines:
        line = line.strip()
        match = re.search(pattern, line)
        if match:
            series = match.group(1)
            raw_title = match.group(2).strip()
            num_match = re.search(r"觀念\s*(\d+)[:：]?(.*)", raw_title)
            if num_match:
                number = num_match.group(1)
                title  = num_match.group(2).strip() or raw_title
            else:
                number = "無編號"
                title  = raw_title
            concepts.append({
                "series": series,
                "number": number,
                "title":  title,
                "full_header": line,
            })
    return concepts


# ─── 來源檔案搜尋 ──────────────────────────────────

def _select_file_manually(candidates: list[str]) -> str | None:
    """讓使用者手動選擇檔案"""
    if not candidates:
        print("❌ 找不到相關檔案")
        return None
    print("\n🔍 請手動選擇檔案：")
    for i, f in enumerate(candidates):
        print(f"   ({i+1}) {os.path.basename(f)}")
    try:
        sel = int(input("編號：")) - 1
        return candidates[sel] if 0 <= sel < len(candidates) else None
    except Exception:
        return None


def find_source_material(
    series: str,
    number: str,
    search_dirs: list[str] | None = None,
) -> str | None:
    """
    智慧搜尋原始素材。
    優先順序：同名 .txt（已快取逐字稿）> 同系列 .mp3 > 手動選擇

    回傳：
        逐字稿文字，找不到回傳 None
    """
    if search_dirs is None:
        search_dirs = [SRC_DIR, os.path.dirname(__file__)]

    if not str(number).isdigit():
        # 找不到數字，手動模式
        all_files = []
        for d in search_dirs:
            all_files += glob.glob(os.path.join(d, "*.mp3"))
            all_files += glob.glob(os.path.join(d, "*.txt"))
        chosen = _select_file_manually(sorted(all_files))
        if not chosen: return None
        if chosen.endswith(".txt"):
            with open(chosen, "r", encoding="utf-8") as f: return f.read()
        return transcribe_audio(chosen)

    num_str = f"{int(number):02d}"
    safe_series = sanitize_filename(series)
    keywords = safe_series.replace("師資班", "").replace("英文學習系統", "") or safe_series

    # 1. 找已快取的 .txt
    for d in search_dirs:
        txts = [f for f in glob.glob(os.path.join(d, f"*{num_str}*.txt"))
                if keywords in sanitize_filename(os.path.basename(f))]
        if txts:
            print(f"   ⏭️  找到逐字稿（省錢）：{os.path.basename(txts[0])}")
            with open(txts[0], "r", encoding="utf-8") as f:
                return f.read()

    # 2. 找 .mp3
    for d in search_dirs:
        mp3s = [f for f in glob.glob(os.path.join(d, f"*{num_str}*.mp3"))
                if keywords in sanitize_filename(os.path.basename(f))]
        if len(mp3s) == 1:
            print(f"   🎵 找到 MP3：{os.path.basename(mp3s[0])}")
            text = transcribe_audio(mp3s[0])
            if text:
                # 快取逐字稿
                cache_path = os.path.splitext(mp3s[0])[0] + ".txt"
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"   💾 已快取逐字稿：{os.path.basename(cache_path)}")
            return text
        elif len(mp3s) > 1:
            chosen = _select_file_manually(mp3s)
            if not chosen: return None
            text = transcribe_audio(chosen)
            return text

    print("   ⚠️  找不到任何檔案，進入手動模式")
    all_files = []
    for d in search_dirs:
        all_files += glob.glob(os.path.join(d, "*.mp3"))
        all_files += glob.glob(os.path.join(d, "*.txt"))
    chosen = _select_file_manually(sorted(all_files))
    if not chosen: return None
    if chosen.endswith(".txt"):
        with open(chosen, "r", encoding="utf-8") as f: return f.read()
    return transcribe_audio(chosen)


# ─── 文案重寫 ──────────────────────────────────────

def optimize_instruction(raw_input: str) -> str:
    """讓 AI 把你的導演指令改寫成精確的 AI 指令"""
    client = _get_client()
    print("✨ AI 秘書正在優化指令...")
    prompt = (
        f"使用者修改文案指令：「{raw_input}」。"
        "請改寫為給 AI 的「最高指導原則」：1. 轉化為具體風格限制。"
        "2. 禁止事項用強烈語氣標示「嚴格禁止」。3. 只回傳改寫後的文字。"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception:
        return raw_input


def rewrite_article(transcript: str, instruction: str) -> str | None:
    """根據導演指令重寫文案"""
    client = _get_client()
    clean = transcript.replace("音速", "音素")
    print("\n🚀 GPT-4o 重寫中...")
    prompt = f"""
你是【蕭博士】的「知識轉譯者」。請修改這篇 LINE OA 文案。

【⚠️ 最高指導原則】：{instruction}

【⛔️ 鐵律】：絕對禁止自創比喻，只能使用逐字稿裡真正提到的例子！

【標準 SOP】：
1. 忠於原味：內容必須基於逐字稿。
2. 標記潤飾：AI 加入的修飾語用【 】包起來。
3. 去標籤化：直接分段，不要出現「內容：」等標籤。
4. 口語化：講人話。

【結構要求】：
第一段（80字）：吸引人的開頭
第二段（250字）：核心教學區
第三段（80字）：以 👉 開頭的溫暖建議

【原始逐字稿】：
{clean[:4000]}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"❌ 重寫失敗：{e}")
        return None


def save_revision(full_header: str, new_content: str, db_file: str = DB_FILE):
    """把修訂版附加到資料庫"""
    with open(db_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n{'='*20} 修訂版（原始：{full_header}）{'='*20}\n")
        f.write(new_content)
        f.write(f"\n{'='*50}\n")
    print(f"✅ 修訂版已附加到 {os.path.basename(db_file)}")


# ─── 主程式 ───────────────────────────────────────

if __name__ == "__main__":
    print("="*60)
    print("  🎬  互動式文案修改工具  (modifier.py)")
    print("="*60)

    while True:
        concepts = load_concepts_from_db()
        if not concepts:
            break

        print(f"\n📖 觀念列表（共 {len(concepts)} 篇）：\n" + "="*60)
        for idx, c in enumerate(concepts):
            num = f"觀念 {c['number']}" if c["number"] != "無編號" else "(無編號)"
            print(f"[{idx+1:3d}] 【{c['series']}】{num}：{c['title']}")
        print("="*60)

        selection = input("\n請輸入要修改的「流水號」（輸入 q 離開）：")
        if selection.lower() == "q":
            print("👋 掰掰！")
            break

        try:
            idx = int(selection) - 1
            if not (0 <= idx < len(concepts)):
                print("❌ 無效編號")
                continue

            target = concepts[idx]
            print(f"\n🎯 選擇：{target['full_header']}")

            # 取得逐字稿
            transcript = find_source_material(target["series"], target["number"])
            if not transcript:
                print("❌ 未取得逐字稿，取消操作")
                continue

            # 導演指令
            raw_cmd = input("\n💡 請輸入修改指令（直接 Enter 使用標準 SOP）：")
            instruction = optimize_instruction(raw_cmd) if raw_cmd else "請依照標準 SOP 重新整理。"
            print(f"\n👉 優化後指令：{instruction}")

            # 重寫
            new_article = rewrite_article(transcript, instruction)
            if new_article:
                print("\n" + "-"*40)
                print(new_article)
                print("-"*40)
                if input("\n保存？(y/n)：").lower() == "y":
                    save_revision(target["full_header"], new_article)

        except ValueError:
            print("❌ 請輸入數字")
