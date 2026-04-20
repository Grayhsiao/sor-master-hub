"""
Global_Skills / common_utils
================================
功能：跨專案共用的小工具函式集合。

用法：
    from Global_Skills.common_utils.common_utils import (
        sanitize_filename,
        create_backup,
        get_next_index,
        smart_separator,
        append_to_database,
    )
"""

import os
import re
import shutil
import datetime

# ─── 檔名工具 ─────────────────────────────────────

def sanitize_filename(name: str) -> str:
    """移除檔名中的非法字元（Windows + macOS 通用）"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


# ─── 資料庫工具 ────────────────────────────────────

def create_backup(db_file: str = "database.txt", backup_dir: str = ".") -> str | None:
    """
    備份資料庫檔案，用時間戳命名。

    參數：
        db_file    : 資料庫檔案路徑（預設 database.txt）
        backup_dir : 備份存放資料夾（預設同目錄）

    回傳：
        備份檔路徑，資料庫不存在回傳 None
    """
    if not os.path.exists(db_file):
        return None
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = os.path.join(backup_dir, f"database_backup_{timestamp}.txt")
    try:
        shutil.copy(db_file, backup_name)
        print(f"📦 已備份：{backup_name}")
        return backup_name
    except Exception as e:
        print(f"⚠️ 備份失敗：{e}")
        return None


def get_next_index(series_name: str, db_file: str = "database.txt") -> int:
    """
    讀取資料庫，找出指定系列目前最大的觀念序號 + 1。

    參數：
        series_name : 系列名稱（如「師資班｜科學實證英文學習系統」）
        db_file     : 資料庫檔案路徑

    回傳：
        下一個可用的觀念序號（整數，最小為 1）
    """
    if not os.path.exists(db_file):
        return 1
    current_max = 0
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = re.escape(f"【{series_name}】觀念") + r"\s*(\d+)"
        for m in re.findall(pattern, content):
            if int(m) > current_max:
                current_max = int(m)
    except Exception:
        pass
    return current_max + 1


def smart_separator(current_series_name: str, db_file: str = "database.txt"):
    """
    若資料庫最後一個系列與目前系列不同，自動插入分隔線。
    （避免不同系列的內容混在一起）

    參數：
        current_series_name : 即將寫入的系列名稱
        db_file             : 資料庫檔案路徑
    """
    if not os.path.exists(db_file):
        return
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return
        matches = re.findall(r"【(.*?)】", content)
        if matches and matches[-1] != current_series_name:
            if not content.endswith("=" * 40):
                with open(db_file, "a", encoding="utf-8") as f:
                    f.write("\n\n" + "=" * 40 + "\n")
    except Exception:
        pass


def append_to_database(content: str, db_file: str = "database.txt") -> bool:
    """
    將內容附加到資料庫檔案。

    參數：
        content : 要寫入的文字內容
        db_file : 資料庫檔案路徑

    回傳：
        成功回傳 True，失敗回傳 False
    """
    try:
        with open(db_file, "a", encoding="utf-8") as f:
            f.write("\n\n" + content + "\n")
        return True
    except Exception as e:
        print(f"❌ 寫入資料庫失敗：{e}")
        return False


def read_or_skip_transcript(mp3_path: str) -> str | None:
    """
    讀取與 MP3 同名的 .txt 逐字稿（若存在）。
    用於跳過已轉錄的檔案，節省 API 費用。

    回傳：
        逐字稿文字，不存在回傳 None
    """
    txt_path = os.path.splitext(mp3_path)[0] + ".txt"
    if os.path.exists(txt_path):
        print(f"   ⏭️  已有逐字稿，直接讀取：{os.path.basename(txt_path)}")
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    return None
