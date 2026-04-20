
import psycopg2
import sys

def recover_chapters():
    print("🔍 正在從 sor_backup.sql 提取章節對照表...")
    mapping = {}
    try:
        with open("sor_backup.sql", "r", encoding="utf-8") as f:
            for line in f:
                if "\t" in line:
                    parts = line.split("\t")
                    if len(parts) > 45:
                        word = parts[1].strip()
                        ch_id = parts[44].strip()
                        ch_name = parts[45].strip()
                        if ch_id != "\\N" and ch_name != "\\N":
                            mapping[word] = (ch_id, ch_name)
    except Exception as e:
        print(f"❌ 讀取 SQL 失敗: {e}")
        return

    print(f"✅ 提取完成，共找到 {len(mapping)} 筆章節對照資料。")

    if not mapping:
        print("⚠️ 未找到任何有效的章節對照，停止更新。")
        return

    print("🚀 正在更新 PostgreSQL 資料庫...")
    try:
        conn = psycopg2.connect(host="localhost", dbname="sor_education", user="gray", password="")
        cur = conn.cursor()
        
        updated_count = 0
        for word, (ch_id, ch_name) in mapping.items():
            cur.execute("""
                UPDATE words 
                SET chapter_700 = %s, chapter_name_700 = %s 
                WHERE word = %s AND (chapter_700 IS NULL OR chapter_700 = '')
            """, (ch_id, ch_name, word))
            updated_count += cur.rowcount
        
        conn.commit()
        print(f"🎉 資料更新成功！共修正了 {updated_count} 筆單字的章節資訊。")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ 資料庫更新失敗: {e}")

if __name__ == "__main__":
    recover_chapters()
