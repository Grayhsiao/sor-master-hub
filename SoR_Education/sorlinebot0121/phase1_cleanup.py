"""
Phase 1 清理腳本 — 移入封存資料夾
=====================================
策略：「移動」而非「刪除」。
所有 Phase 1 的目標都會被搬到 _archive_phase1/ 資料夾。
待新系統測試完畢，再手動刪除整個 _archive_phase1/ 即可。
"""

import os
import shutil
import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_DIR = os.path.join(BASE, "_archive_phase1")

# 確保封存資料夾存在
os.makedirs(ARCHIVE_DIR, exist_ok=True)

print(f"🚀 Phase 1 封存開始...")
print(f"📦 備份 zip 已存在：PHASE1_BACKUP_20260305_062044.zip")
print(f"📁 封存目的地：{ARCHIVE_DIR}\n")

moved = 0
failed = 0

def move_to_archive(src_rel, label=""):
    """把 src_rel（相對 BASE 的路徑）移入 _archive_phase1/"""
    global moved, failed
    src = os.path.join(BASE, src_rel)
    dst = os.path.join(ARCHIVE_DIR, src_rel)

    if not os.path.exists(src):
        print(f"   ⚪ 不存在（跳過）：{src_rel}")
        return

    os.makedirs(os.path.dirname(dst), exist_ok=True)

    try:
        shutil.move(src, dst)
        tag = f"  [{label}]" if label else ""
        print(f"   ✅ 已封存{tag}：{src_rel}")
        moved += 1
    except Exception as e:
        print(f"   ❌ 失敗：{src_rel} → {e}")
        failed += 1

# ──────────────────────────────────────────
# Group 1：空 / 幾乎空的資料夾
# ──────────────────────────────────────────
print("=" * 55)
print("【Group 1】空資料夾")
print("=" * 55)
for folder in ["openclaw", "test", "total_solution", "toy", "test1", "upload"]:
    move_to_archive(folder, "空資料夾")

# ──────────────────────────────────────────
# Group 2：備份快照（本身就是舊備份）
# ──────────────────────────────────────────
print("\n" + "=" * 55)
print("【Group 2】舊備份快照資料夾")
print("=" * 55)
for folder in ["FocusGuardv1_Backup_2026-03-04", "_backup_20260217"]:
    move_to_archive(folder, "舊備份")

# ──────────────────────────────────────────
# Group 3：舊版 FocusGuard（被 FocusGuardv1 取代）
# ──────────────────────────────────────────
print("\n" + "=" * 55)
print("【Group 3】舊版 App（FocusGuard）")
print("=" * 55)
move_to_archive("FocusGuard", "舊版App")

# ──────────────────────────────────────────
# Group 4：sorlinebot0121 內的重複腳本
# ──────────────────────────────────────────
print("\n" + "=" * 55)
print("【Group 4】sorlinebot0121 內的重複/暫存腳本")
print("=" * 55)
duplicate_scripts = [
    "sorlinebot0121/multi_makerv1.py",         # 被 v2 取代
    "sorlinebot0121/multi_maker_long_1.py",    # 同 long 只差 URL
    "sorlinebot0121/rewrite_concept_1.py",     # 被 skip_music 版取代
    "sorlinebot0121/fb_archiver.py",           # 被 fb_browser_full 取代
    "sorlinebot0121/fb_iphone_mode.py",        # 只是換 User-Agent 的實驗版
    "sorlinebot0121/未命名2.rtf",
    "sorlinebot0121/未命名5.rtf",
    "sorlinebot0121/未命名7.txt",
    "sorlinebot0121/未命名8.txt",
    "sorlinebot0121/未命名檔案夾",
    "sorlinebot0121/all_pqosts.txt",           # typo 版
    "sorlinebot0121/all_pqosts拷貝.txt",       # typo 版的拷貝
]
for path in duplicate_scripts:
    move_to_archive(path, "重複/暫存")

# ──────────────────────────────────────────
# Group 5：舊版 database_backup（留最新 2 個）
# ──────────────────────────────────────────
print("\n" + "=" * 55)
print("【Group 5】sorlinebot0121 舊版資料庫備份（保留最新 2 個）")
print("=" * 55)
old_backups = [
    "sorlinebot0121/database_backup_20260123_094529.txt",
    "sorlinebot0121/database_backup_20260125_082848.txt",
    "sorlinebot0121/database_backup_20260125_083659.txt",
    "sorlinebot0121/database_backup_20260125_123540.txt",
    "sorlinebot0121/database_backup_20260125_191030.txt",
    "sorlinebot0121/database_backup_20260125_191715.txt",
    "sorlinebot0121/database_backup_20260125_191813.txt",
    "sorlinebot0121/database_backup_20260125_192314.txt",
    # 保留最新 2 個：193719, 20260127 不動
]
for path in old_backups:
    move_to_archive(path, "舊備份")

# ──────────────────────────────────────────
# Group 6：sor_line_db_bot 內的重複腳本
# ──────────────────────────────────────────
print("\n" + "=" * 55)
print("【Group 6】sor_line_db_bot 內的重複腳本")
print("=" * 55)
for path in [
    "sor_line_db_bot/multi_maker.py",      # 同 sorlinebot0121/multi_makerv1
    "sor_line_db_bot/忠於原味版.py",       # 實驗草稿（已有 multi_maker012108 正式版）
]:
    move_to_archive(path, "重複")

# ──────────────────────────────────────────
# 完成報告
# ──────────────────────────────────────────
print("\n" + "=" * 55)
print(f"🎉 Phase 1 封存完成！")
print(f"   ✅ 成功封存：{moved} 個項目")
if failed:
    print(f"   ❌ 失敗：{failed} 個項目")
print(f"\n📁 所有封存項目位於：")
print(f"   {ARCHIVE_DIR}")
print(f"\n💡 後續步驟：")
print(f"   1. 測試新系統（Phase 2 → Phase 3 → Phase 4）")
print(f"   2. 確認一切正常後，刪除整個 _archive_phase1/ 資料夾即可")
print(f"   3. 如需還原任何檔案，也可從 PHASE1_BACKUP_20260305_062044.zip 解壓")
