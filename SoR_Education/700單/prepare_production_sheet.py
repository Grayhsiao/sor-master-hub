import pandas as pd
import os

# --- 設定 ---
MASTER_EXCEL = "字典底層資料 的副本.xlsx"
OUTPUT_EXCEL = "700單_量產清單.xlsx"

def create_production_sheet():
    if not os.path.exists(MASTER_EXCEL):
        print(f"❌ 找不到原始檔案: {MASTER_EXCEL}")
        return

    print(f"📂 正在讀取底層資料: {MASTER_EXCEL}")
    
    # 讀取 master Excel (跳過中文標頭列)
    df_master = pd.read_excel(MASTER_EXCEL).fillna("")
    df_data = df_master.iloc[1:] # 第一列是中文標頭

    # 1. 提取核心資料
    # 我們需要 word, minum, Chinese, 以及用來篩選與排序的 700Id
    needed_cols = ["word", "minum", "Chinese", "700Id"]
    
    # 檢查欄位是否存在
    for col in needed_cols:
        if col not in df_data.columns:
            print(f"⚠️ 警告: 原始檔案中缺少欄位 '{col}'")
            df_data[col] = ""

    # 2. 針對「700單」進行優化
    # 轉換 700Id 為數值，以便正確排序
    df_data["700Id_numeric"] = pd.to_numeric(df_data["700Id"], errors='coerce')
    
    # 篩選出 700Id 有值的列 (即 700單核心單字)
    df_production = df_data[df_data["700Id_numeric"].notna()].copy()
    
    # 按 700Id 排序
    df_production = df_production.sort_values(by="700Id_numeric")

    # 3. 新增量產控制欄位
    df_production["Order"] = "word ph01 Chinese" # 預設順序
    df_production["Sentence1"] = ""
    df_production["Sentence2"] = ""
    
    # 4. 欄位重新排序 (讓 Order 與 700Id 在前面，方便博士編輯)
    cols = ["700Id", "word", "Order", "minum", "Chinese", "Sentence1", "Sentence2"]
    df_production = df_production[cols]

    # 儲存
    df_production.to_excel(OUTPUT_EXCEL, index=False)
    print(f"✅ 700單專屬量產清單已生成: {OUTPUT_EXCEL}")
    print(f"📈 總計提取出 {len(df_production)} 個核心單字，已按編號排序。")

if __name__ == "__main__":
    create_production_sheet()
