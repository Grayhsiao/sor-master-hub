import re
import json

SQL_FILE = "sor_backup.sql"
OUTPUT_JSON = "scratch/chapters_map.json"

def extract_chapters():
    mapping = {}
    print(f"Reading {SQL_FILE}...")
    try:
        count = 0
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # 只處理包含多個 Tab 的資料列
                if line.count('\t') > 45:
                    parts = line.split('\t')
                    # id_700 is at index 43, chapter_700 at index 44
                    id_700 = parts[43].strip()
                    chapter = parts[44].strip()
                    name = parts[45].strip()
                    category = parts[46].strip()
                    word = parts[1].strip()
                    
                    if id_700 and id_700 != '\\N' and chapter and chapter != '\\N':
                        mapping[id_700] = {
                            "word": word,
                            "chapter": chapter,
                            "name": name,
                            "category": category
                        }
        
        print(f"Extracted {len(mapping)} 700-word chapter mappings.")
        
        # 抽樣列印前 5 筆
        first_keys = list(mapping.keys())[:5]
        for k in first_keys:
            print(f"  {k}: {mapping[k]}")
            
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"Success! Map saved to {OUTPUT_JSON}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_chapters()
