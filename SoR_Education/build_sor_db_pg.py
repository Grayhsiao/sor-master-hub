"""
SoR 知識庫 - PostgreSQL 母體資料導入腳本 (v2.0)
================================================
將「字典底層資料.xlsx」完整導入 PostgreSQL 資料庫。
本機資料庫: sor_education (localhost)
執行方式: python3 build_sor_db_pg.py
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# ─── 連線設定 ─────────────────────────────────────────────────
PG_HOST   = "localhost"
PG_PORT   = 5432
PG_DB     = "sor_education"
PG_USER   = os.environ.get("USER", "gray")  # 自動抓 Mac 登入名
PG_PASS   = ""  # 本機預設不需要密碼

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "700單", "字典底層資料 的副本.xlsx")

# ─── 欄位映射：原始欄名 → DB 欄名 ──────────────────────────────
COLUMN_MAP = {
    # 核心識別
    "id":               "sor_id",
    "word":             "word",
    "Syllables":        "syllables",
    "Frequency":        "frequency",
    "Hyphenation":      "hyphenation",
    # 中文釋義
    "Chinese":          "chinese_pub",
    "trans_zh":         "trans_zh",
    # 詞性
    "n":                "pos_n",
    "nc":               "pos_nc",
    "nu":               "pos_nu",
    "v":                "pos_v",
    "vt":               "pos_vt",
    "vi":               "pos_vi",
    "adj":              "pos_adj",
    "adv":              "pos_adv",
    "POS":              "pos_code",
    # 音標 (最核心)
    "KK":               "kk",
    "IPA":              "ipa",
    "MiBopomofo":       "mi_bopomofo",
    "Intonation":       "intonation",
    "StressedVowel_KK": "stressed_vowel_kk",
    "StressedVowel_Mi": "stressed_vowel_mi",
    # SoR PA 核心
    "HC":               "hc",
    "V":                "v_vowel",
    "TC":               "tc",
    "MBHC":             "mb_hc",
    "MBV":              "mb_v",
    "MBTC":             "mb_tc",
    "minum":            "minum",
    "Spellego_44":      "spellego_44",
    "Spellego_66":      "spellego_66",
    # 音檔
    "voice":            "audio_file",
    "Audio1":           "audio_native",
    "Audio2":           "audio_hc",
    "Audio3":           "audio_v",
    "Audio4":           "audio_tc",
    "Audio5":           "audio_slow",
    "breakdown":        "breakdown",
    # 教材定位
    "6KPages":          "pages_6k",
    "6KGrid":           "grid_6k",
    "6KVCat":           "vcat_6k",
    "8KPages":          "pages_8k",
    "8KGrid":           "grid_8k",
    "700Id":            "id_700",
    "700Chapter":       "chapter_700",
    "700ChapterName":   "chapter_name_700",
    "700Category":      "category_700",
    "700Pages":         "pages_700",
    "700Grid":          "grid_700",
    # 學習分級
    "2K":               "grade_2k",
    "JuniorHigh":       "grade_junior",
    "SeniorHigh":       "grade_senior",
    "GEPT":             "grade_gept",
}

def clean_value(val):
    """清理 NaN、#REF! 等無效值"""
    if pd.isna(val):   return None
    s = str(val).strip()
    if s in ('#REF!', '#N/A', 'nan', 'NaN', ''): return None
    if s == 'Yes':     return True
    if s == 'No':      return False
    return s

def main():
    print("=" * 58)
    print("  SoR 知識庫 PostgreSQL 建立工具 v2.0")
    print("=" * 58)

    # ─── 1. 讀取 Excel ────────────────────────────────────────
    print(f"\n📖 讀取 Excel 檔案...")
    if not os.path.exists(EXCEL_PATH):
        print(f"\n❌ 找不到檔案：{EXCEL_PATH}")
        sys.exit(1)

    # row 0 = 英文欄名, row 1 = 中文說明(跳過), row 2+ = 資料
    raw_df = pd.read_excel(EXCEL_PATH, header=0, skiprows=[1], dtype=str)
    print(f"   ✅ 共 {len(raw_df):,} 筆，{len(raw_df.columns)} 個欄位")

    # ─── 2. 選欄 & 重命名 ─────────────────────────────────────
    available = [c for c in COLUMN_MAP if c in raw_df.columns]
    df = raw_df[available].copy()
    df.rename(columns={k: COLUMN_MAP[k] for k in available}, inplace=True)
    print(f"   📊 匯入欄位：{len(df.columns)} 個")

    # ─── 3. 清理 ──────────────────────────────────────────────
    print(f"\n🧹 清理無效資料...")
    df = df.map(clean_value)
    df = df[df['word'].notna() & (df['word'] != '單字')]
    df = df.reset_index(drop=True)
    print(f"   ✅ 有效資料：{len(df):,} 筆")

    # ─── 4. 連接 PostgreSQL ───────────────────────────────────
    print(f"\n🗃️  連接 PostgreSQL ({PG_HOST}/{PG_DB})...")
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT,
            dbname=PG_DB, user=PG_USER, password=PG_PASS
        )
        conn.autocommit = False
        cursor = conn.cursor()
        print(f"   ✅ 連線成功")
    except Exception as e:
        print(f"\n❌ 連線失敗：{e}")
        sys.exit(1)

    # ─── 5. 建立資料表 ────────────────────────────────────────
    print(f"\n📐 建立資料表 words...")
    cursor.execute("DROP TABLE IF EXISTS words CASCADE")
    
    # 動態依照 df 的欄位生成建表語法
    col_defs = []
    for col in df.columns:
        if col in ('pos_n','pos_nc','pos_nu','pos_v','pos_vt','pos_vi',
                   'pos_adj','pos_adv'):
            col_defs.append(f'"{col}" BOOLEAN')
        elif col == 'sor_id':
            col_defs.append(f'"{col}" INTEGER PRIMARY KEY')
        elif col in ('frequency','syllables'):
            col_defs.append(f'"{col}" INTEGER')
        else:
            col_defs.append(f'"{col}" TEXT')

    create_sql = f"CREATE TABLE words (\n  {','.join(chr(10)+'  ' + c for c in col_defs)}\n)"
    cursor.execute(create_sql)
    print(f"   ✅ 資料表建立完成")

    # ─── 6. 批次寫入 ──────────────────────────────────────────
    print(f"\n⬆️  寫入資料中（{len(df):,} 筆）...")
    cols = [f'"{c}"' for c in df.columns]
    insert_sql = f"INSERT INTO words ({', '.join(cols)}) VALUES %s ON CONFLICT DO NOTHING"
    
    # 分批寫入，避免單次 query 太大
    batch_size = 500
    total = 0
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        rows  = [tuple(r) for r in batch.itertuples(index=False)]
        execute_values(cursor, insert_sql, rows)
        total += len(rows)
        print(f"   進度：{total:,} / {len(df):,}", end="\r")
    
    print(f"\n   ✅ 寫入完成")

    # ─── 7. 建立搜尋索引 ──────────────────────────────────────
    print(f"\n⚡ 建立索引...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_word    ON words("word")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_id_700  ON words("id_700")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_junior  ON words("grade_junior")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gept    ON words("grade_gept")')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_minum   ON words USING gin(to_tsvector(\'simple\', COALESCE("minum",\'\')))')
    print(f"   ✅ 索引建立完成")

    conn.commit()

    # ─── 8. 驗證 ──────────────────────────────────────────────
    print(f"\n🔬 驗證...")
    cursor.execute("SELECT COUNT(*) FROM words")
    count = cursor.fetchone()[0]
    cursor.execute('SELECT word, kk, minum, intonation FROM words WHERE word=\'bed\'')
    sample = cursor.fetchone()

    print(f"   ✅ 資料庫總筆數：{count:,} 筆")
    if sample:
        print(f"   🔍 抽樣 'bed'：")
        for label, val in zip(['word','kk','minum','intonation'], sample):
            print(f"      {label:12s}: {val}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 58)
    print(f"  🎉 SoR 知識庫建立完成！")
    print(f"  📊 資料庫：{PG_DB} @ {PG_HOST}")
    print(f"  📋 資料表：words ({count:,} 筆, {len(df.columns)} 欄)")
    print("=" * 58)

if __name__ == "__main__":
    main()
