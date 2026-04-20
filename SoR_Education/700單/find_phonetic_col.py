import pandas as pd

file_path = "字典底層資料 的副本.xlsx"
try:
    df = pd.read_excel(file_path)
    # 尋找名稱中包含 '音標' 或 '專利' 的欄位
    target_cols = [col for col in df.columns if '音標' in str(col) or '專利' in str(col)]
    
    print(f"找到的核心欄位: {target_cols}")
    
    # 預覽這些欄位的內容
    if target_cols:
        print("\n樣本資料 (前 10 筆):")
        # 篩選掉 700Id 為空的，因為我們優先處理 700 單
        sample_df = df[df['700Id'].notna()][['700Id', 'word'] + target_cols].head(10)
        print(sample_df)
    else:
        print("\n未找到包含「音標」或「專利」字樣的欄位，改列出所有欄位名稱搜尋:")
        print(df.columns.tolist())
        
except Exception as e:
    print(f"發生錯誤: {e}")
