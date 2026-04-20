
import pandas as pd
import psycopg2
import os

def recover_chapters_from_excel():
    excel_path = "700單/字典底層資料 的副本.xlsx"
    print(f"📖 正在從 {excel_path} 讀取章節資料...")
    
    if not os.path.exists(excel_path):
        print(f"❌ 找不到 Excel 檔案: {excel_path}")
        return

    try:
        # 讀取 Excel，row 0 是欄名
        df = pd.read_excel(excel_path)
        print(f"   ✅ Excel 讀取完成，共 {len(df)} 筆。")
        
        # 過濾出有章節資訊的行
        # 注意：Excel 裡面可能是 #REF!，我們需要過濾掉
        valid_df = df[df['700Chapter'].notna() & (df['700Chapter'] != '#REF!') & (df['word'].notna())]
        print(f"   ✅ 找到 {len(valid_df)} 筆有效的章節對照資料。")
        
    except Exception as e:
        print(f"❌ 讀取 Excel 失敗: {e}")
        return

    if valid_df.empty:
        print("⚠️ 未找到任何有效的章節對照，停止更新。")
        return

    print("🚀 正在更新 PostgreSQL 資料庫...")
    try:
        conn = psycopg2.connect(host="localhost", dbname="sor_education", user="gray", password="")
        cur = conn.cursor()
        
        updated_count = 0
        for _, row in valid_df.iterrows():
            word = str(row['word']).strip()
            ch_id = str(row['700Chapter']).strip()
            ch_name = str(row['700ChapterName']).strip()
            
            cur.execute("""
                UPDATE words 
                SET chapter_700 = %s, chapter_name_700 = %s 
                WHERE word = %s
            """, (ch_id, ch_name, word))
            updated_count += cur.rowcount
        
        conn.commit()
        print(f"🎉 資料更新成功！共修正了 {updated_count} 筆單字的章節資訊。")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ 資料庫更新失敗: {e}")

if __name__ == "__main__":
    recover_chapters_from_excel()
