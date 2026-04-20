import pandas as pd
import re

file_path = "字典底層資料 的副本.xlsx"
try:
    df = pd.read_excel(file_path)
    
    # 鎖定有 700Id 的資料進行分析
    df_700 = df[df['700Id'].notna()]
    
    print(f"分析 700 單資料共 {len(df_700)} 筆\n")
    
    # 定義一個函數來檢查是否看起來像音標號碼序列 (例如 "12 34 5" 或 12)
    def looks_like_phonetic_seq(val):
        s = str(val).strip()
        if not s or s == 'nan': return False
        # 尋找是否包含 1-85 之間的數字
        nums = re.findall(r'\d+', s)
        if not nums: return False
        # 檢查數字是否都在 1-85 範圍內
        try:
            return all(1 <= int(n) <= 85 for n in nums)
        except:
            return False

    candidate_cols = []
    for col in df_700.columns:
        # 計算該欄位符合音標序列特的比例
        matches = df_700[col].apply(looks_like_phonetic_seq)
        match_rate = matches.mean()
        if match_rate > 0.5: # 如果超過 50% 符合
            candidate_cols.append((col, match_rate))
    
    print("潛在的專利音標欄位 (按符合率排序):")
    for col, rate in sorted(candidate_cols, key=lambda x: x[1], reverse=True):
        print(f"- {col}: {rate:.2%}")
        print(f"  範例內容: {df_700[col].head(5).tolist()}\n")

    # 同時檢查 breakdown 欄位，因為它可能包含分鏡或音標資訊
    if 'breakdown' in df.columns:
        print("breakdown 欄位預覽:")
        print(df_700['breakdown'].head(10).tolist())

except Exception as e:
    print(f"發生錯誤: {e}")
