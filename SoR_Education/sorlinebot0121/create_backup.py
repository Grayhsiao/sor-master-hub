"""
備份腳本 — Phase 1 清理備份
============================
此腳本會把「Phase 1 待刪除」的所有資料夾與檔案，
打包成一個帶時間戳的 .zip 壓縮檔，存放在 python project/ 根目錄。
執行後不會刪除任何東西，只是備份。
"""

import os
import zipfile
import datetime

# 根目錄
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# 待備份清單（Phase 1 所有標記刪除的目標）
# ==========================================
TARGETS = [
    # 空資料夾 / 幾乎空資料夾
    os.path.join(BASE, "openclaw"),
    os.path.join(BASE, "test"),
    os.path.join(BASE, "total_solution"),
    os.path.join(BASE, "toy"),
    os.path.join(BASE, "test1"),

    # 備份資料夾（本身就是備份，但備份備份才安全）
    os.path.join(BASE, "FocusGuardv1_Backup_2026-03-04"),
    os.path.join(BASE, "_backup_20260217"),

    # 舊版 FocusGuard（被 FocusGuardv1 取代）
    os.path.join(BASE, "FocusGuard"),

    # sorlinebot0121 內的重複腳本
    os.path.join(BASE, "sorlinebot0121", "multi_makerv1.py"),
    os.path.join(BASE, "sorlinebot0121", "multi_maker_long_1.py"),
    os.path.join(BASE, "sorlinebot0121", "rewrite_concept_1.py"),
    os.path.join(BASE, "sorlinebot0121", "fb_archiver.py"),
    os.path.join(BASE, "sorlinebot0121", "fb_iphone_mode.py"),
    os.path.join(BASE, "sorlinebot0121", "未命名2.rtf"),
    os.path.join(BASE, "sorlinebot0121", "未命名5.rtf"),
    os.path.join(BASE, "sorlinebot0121", "未命名7.txt"),
    os.path.join(BASE, "sorlinebot0121", "未命名8.txt"),
    os.path.join(BASE, "sorlinebot0121", "未命名檔案夾"),
    os.path.join(BASE, "sorlinebot0121", "all_pqosts.txt"),
    os.path.join(BASE, "sorlinebot0121", "all_pqosts拷貝.txt"),

    # sorlinebot0121 舊版資料庫備份（只保留最新兩個，備份其餘）
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260123_094529.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_082848.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_083659.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_123540.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_191030.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_191715.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_191813.txt"),
    os.path.join(BASE, "sorlinebot0121", "database_backup_20260125_192314.txt"),

    # sor_line_db_bot 內的重複腳本
    os.path.join(BASE, "sor_line_db_bot", "multi_maker.py"),
    os.path.join(BASE, "sor_line_db_bot", "忠於原味版.py"),
    os.path.join(BASE, "sor_line_db_bot", "未命名2.txt"),
    os.path.join(BASE, "sor_line_db_bot", "未命名2ㄅ.txt"),

    # upload 空骨架
    os.path.join(BASE, "upload"),
]

# ==========================================
# 執行備份
# ==========================================
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
zip_name = f"PHASE1_BACKUP_{timestamp}.zip"
zip_path = os.path.join(BASE, zip_name)

print(f"🚀 開始備份 Phase 1 待清理項目...")
print(f"📦 壓縮檔：{zip_path}\n")

added = 0
skipped = 0

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for target in TARGETS:
        if not os.path.exists(target):
            print(f"   ⚪ 不存在（跳過）：{os.path.relpath(target, BASE)}")
            skipped += 1
            continue

        if os.path.isfile(target):
            arcname = os.path.relpath(target, BASE)
            zf.write(target, arcname)
            print(f"   ✅ 備份檔案：{arcname}")
            added += 1

        elif os.path.isdir(target):
            for root, dirs, files in os.walk(target):
                # 排除 __pycache__ 和 .git 等暫存資料夾
                dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "build", "dist", ".venv"}]
                for file in files:
                    if file == ".DS_Store":
                        continue
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, BASE)
                    zf.write(full_path, arcname)
                    added += 1
            dir_rel = os.path.relpath(target, BASE)
            print(f"   ✅ 備份資料夾：{dir_rel}/")

print(f"\n{'='*50}")
print(f"🎉 備份完成！")
print(f"   📁 備份項目：{added} 個檔案，{skipped} 個不存在跳過")
print(f"   📦 壓縮檔位置：{zip_path}")
zip_size_mb = os.path.getsize(zip_path) / 1024 / 1024
print(f"   💾 壓縮檔大小：{zip_size_mb:.2f} MB")
print(f"\n✅ 備份完成後，再執行 phase1_cleanup.py 即可安全刪除。")
