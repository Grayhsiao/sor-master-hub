import pandas as pd

file_path = "字典底層資料 的副本.xlsx"
try:
    # 讀取 Excel 檔案的所有 Sheet 內容
    xl = pd.ExcelFile(file_path)
    print(f"Sheet 名稱: {xl.sheet_names}")
    
    # 讀取第一個 Sheet 作為樣本分析
    df = pd.read_excel(xl, sheet_name=xl.sheet_names[0])
    print("\n前 5 筆資料預覽:")
    print(df.head())
    print("\n欄位列表:")
    print(df.columns.tolist())
    print("\n欄位型別與非空值統計:")
    print(df.info())
except Exception as e:
    print(f"發生錯誤: {e}")
