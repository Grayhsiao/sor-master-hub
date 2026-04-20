import json
import psycopg2
import os

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "sor_education",
    "user": os.environ.get("USER", "gray"),
    "password": ""
}

JSON_FILE = "scratch/chapters_map.json"

def patch_chapters():
    if not os.path.exists(JSON_FILE):
        print(f"❌ 找不到檔案: {JSON_FILE}")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    print(f"準備更新 {len(mapping)} 筆單字資料...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        updated_count = 0
        for id_700, data in mapping.items():
            # Update chapter_700, chapter_name_700, category_700
            sql = """
                UPDATE words 
                SET chapter_700 = %s, 
                    chapter_name_700 = %s, 
                    category_700 = %s
                WHERE id_700 = %s
            """
            cursor.execute(sql, (data['chapter'], data['name'], data['category'], str(id_700)))
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"  ✅ 已更新: {id_700} ({data['word']}) -> {data['name']}")
        
        conn.commit()
        print(f"\n🚀 修復完成！成功更新 {updated_count} 筆資料。")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    patch_chapters()
