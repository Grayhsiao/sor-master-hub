import pandas as pd
import ast

file_path = "字典底層資料 的副本.xlsx"
try:
    df = pd.read_excel(file_path)
    df_700 = df[df['700Id'].notna()]
    
    # 檢查 minum 欄位
    print("minum 欄位樣本:")
    print(df_700['minum'].head(10).tolist())
    
    # 檢查 Spellego_66 欄位 (解析 JSON-like 字串)
    print("\nSpellego_66 欄位樣本 (解析後):")
    for val in df_700['Spellego_66'].head(5):
        try:
            # 有些可能是字串形式的 list
            if isinstance(val, str) and val.startswith('['):
                parsed = ast.literal_eval(val)
                print(parsed)
            else:
                print(val)
        except:
            print(val)

except Exception as e:
    print(f"發生錯誤: {e}")
