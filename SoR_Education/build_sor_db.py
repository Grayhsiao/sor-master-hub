"""
SoR 知識庫 - 母體資料導入腳本 (v1.0)
====================================
將「字典底層資料.xlsx」完整導入 SQLite 資料庫。
資料庫位置: SoR_Education/sor_master.db
執行方式: python3 build_sor_db.py
"""

import pandas as pd
import sqlite3
import os
import sys

# ─── 路徑設定 ─────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH  = os.path.join(BASE_DIR, "Vocab_700", "字典底層資料 的副本.xlsx")
DB_PATH     = os.path.join(BASE_DIR, "sor_master.db")

# ─── 欄位映射：原始欄名 → 資料庫欄名（加中文說明） ──────────────
# 格式: 原始欄名 : (DB欄名, 欄位說明)
COLUMN_MAP = {
    # ── 核心識別欄 ──
    "id":               ("id",                "身份證 (主鍵)"),
    "word":             ("word",              "單字"),
    "Syllables":        ("syllables",         "音節數"),
    "Frequency":        ("frequency",         "使用頻率排名"),
    "Hyphenation":      ("hyphenation",       "分音節拼法"),

    # ── 中文釋義 ──
    "Chinese":          ("chinese_pub",       "中文翻譯 (出版品版)"),
    "trans_zh":         ("trans_zh",          "中文翻譯 (標準版)"),

    # ── 詞性欄 (直接從 Yes/No 轉 bool) ──
    "n":                ("pos_n",             "名詞"),
    "nc":               ("pos_nc",            "可數名詞"),
    "nu":               ("pos_nu",            "不可數名詞"),
    "v":                ("pos_v",             "動詞"),
    "vt":               ("pos_vt",            "及物動詞"),
    "vi":               ("pos_vi",            "不及物動詞"),
    "adj":              ("pos_adj",           "形容詞"),
    "adv":              ("pos_adv",           "副詞"),
    "POS":              ("pos_code",          "詞性代碼"),

    # ── 音標欄 (最核心) ──
    "KK":               ("kk",               "KK 音標"),
    "IPA":              ("ipa",              "IPA 音標"),
    "MiBopomofo":       ("mi_bopomofo",      "雙語注音"),
    "Intonation":       ("intonation",       "語調 (e.g. 4, 1..)"),
    "StressedVowel_KK": ("stressed_vowel_kk","重音節母音 (KK)"),
    "StressedVowel_Mi": ("stressed_vowel_mi","重音節母音 (Mi)"),

    # ── SoR PA 核心欄 ──
    "HC":               ("hc",               "頭子音 (英文)"),
    "V":                ("v_vowel",          "母音 (英文)"),
    "TC":               ("tc",               "尾子音 (英文)"),
    "MBHC":             ("mb_hc",            "雙語注音頭子音"),
    "MBV":              ("mb_v",             "雙語注音母音"),
    "MBTC":             ("mb_tc",            "雙語注音尾子音"),
    "minum":            ("minum",            "專利音標 JSON 陣列"),
    "Spellego_44":      ("spellego_44",      "奇積木音標 (44音)"),
    "Spellego_66":      ("spellego_66",      "奇積木音標 (66音)"),

    # ── 音檔欄 ──
    "voice":            ("audio_file",       "主音檔檔名"),
    "Audio1":           ("audio_native",     "母語人完整錄音"),
    "Audio2":           ("audio_hc",         "頭子音音檔"),
    "Audio3":           ("audio_v",          "母音音檔"),
    "Audio4":           ("audio_tc",         "尾子音音檔"),
    "Audio5":           ("audio_slow",       "慢速錄音"),
    "breakdown":        ("breakdown",        "分解音檔清單"),

    # ── 教材定位欄 ──
    "6KPages":          ("pages_6k",         "6K字典頁數"),
    "6KGrid":           ("grid_6k",          "6K字典位置"),
    "6KVCat":           ("vcat_6k",          "6K母音分類"),
    "8KPages":          ("pages_8k",         "8K字典頁數"),
    "8KGrid":           ("grid_8k",          "8K字典位置"),
    "700Id":            ("id_700",           "700單編號"),
    "700Chapter":       ("chapter_700",      "700單章節"),
    "700ChapterName":   ("chapter_name_700", "700章節名稱"),
    "700Category":      ("category_700",     "700分類"),
    "700Pages":         ("pages_700",        "700單頁數"),
    "700Grid":          ("grid_700",         "700單位置"),

    # ── 學習分級欄 ──
    "2K":               ("grade_2k",         "高中2000字"),
    "JuniorHigh":       ("grade_junior",     "國中"),
    "SeniorHigh":       ("grade_senior",     "高中"),
    "GEPT":             ("grade_gept",       "全民英檢"),
}

def clean_value(val):
    """清理 NaN、#REF! 等無效值"""
    if pd.isna(val): return None
    s = str(val).strip()
    if s in ('#REF!', '#N/A', 'nan', 'NaN', ''): return None
    if s == 'Yes': return 1
    if s == 'No':  return 0
    return s

def main():
    print("=" * 55)
    print("  SoR 母體資料庫建立工具 v1.0")
    print("=" * 55)

    # ─── 1. 讀取 Excel ─────────────────────────────────────
    print(f"\n📖 讀取 Excel 檔案...")
    print(f"   路徑：{EXCEL_PATH}")

    if not os.path.exists(EXCEL_PATH):
        print(f"\n❌ 找不到檔案！請確認路徑正確。")
        sys.exit(1)

    # row 0 = 英文欄名, row 1 = 中文說明(跳過), row 2+ = 真實資料
    raw_df = pd.read_excel(EXCEL_PATH, header=0, skiprows=[1], dtype=str)
    print(f"   ✅ 讀取完成！共 {len(raw_df):,} 筆資料，{len(raw_df.columns)} 個欄位。")

    # ─── 2. 只選擇 COLUMN_MAP 裡面有定義的欄 ─────────────────
    available_cols = [c for c in COLUMN_MAP.keys() if c in raw_df.columns]
    df = raw_df[available_cols].copy()
    df.rename(columns={k: v[0] for k, v in COLUMN_MAP.items() if k in df.columns}, inplace=True)
    print(f"   📊 選取欄位數：{len(df.columns)} 個")

    # ─── 3. 清理資料 ──────────────────────────────────────────
    print(f"\n🧹 清理資料中（移除 #REF!、NaN 等無效值）...")
    df = df.map(clean_value)

    # 移除 word 為空的行 (標題說明行)
    df = df[df['word'].notna() & (df['word'] != '單字')]
    df = df.reset_index(drop=True)
    print(f"   ✅ 清理後剩餘：{len(df):,} 筆有效資料")

    # ─── 4. 建立/連接 SQLite ───────────────────────────────────
    print(f"\n🗃️  建立資料庫...")
    print(f"   路徑：{DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 先清空舊表格（若存在）
    cursor.execute("DROP TABLE IF EXISTS words")

    # 寫入資料
    df.to_sql("words", conn, if_exists="replace", index=False)
    conn.commit()

    # ─── 5. 建立索引 (加速搜尋) ────────────────────────────────
    print(f"\n⚡ 建立搜尋索引...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON words(word)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_700id ON words(id_700)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_grade_junior ON words(grade_junior)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_grade_gept ON words(grade_gept)")
    conn.commit()
    print(f"   ✅ 索引建立完成")

    # ─── 6. 驗證 ──────────────────────────────────────────────
    print(f"\n🔬 驗證資料庫...")
    count = cursor.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    sample = cursor.execute(
        "SELECT word, kk, minum, intonation, grade_junior, grade_gept FROM words WHERE word='bed' LIMIT 1"
    ).fetchone()

    print(f"   ✅ 資料庫總筆數：{count:,} 筆")
    print(f"\n   🔍 抽樣驗證 'bed'：")
    if sample:
        labels = ['word', 'kk', 'minum', 'intonation', 'grade_junior', 'grade_gept']
        for label, val in zip(labels, sample):
            print(f"      {label:15s}: {val}")

    conn.close()

    print("\n" + "=" * 55)
    print(f"  ✅ 資料庫建立完成！")
    print(f"  📁 {DB_PATH}")
    print(f"  📊 可使用 DB Browser for SQLite 打開查看")
    print("=" * 55)

if __name__ == "__main__":
    main()
