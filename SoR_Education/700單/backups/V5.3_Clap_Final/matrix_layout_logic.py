import math

def distribute_to_three_rows(minum_data):
    """
    將多層級的 minum 數據壓縮成固定的 3 排。
    minum_data 格式例: [[[1],[59]], [[15]], [[4]]]
    """
    if not minum_data or not isinstance(minum_data, list):
        return [[], [], []]
    
    n = len(minum_data)
    
    if n <= 3:
        # 少於三排則直接填入，不足補空
        result = minum_data + [[]] * (3 - n)
        return result
    
    # 若大於 3 排，進行平攤分配
    # 計算每排應該分到幾個子層級
    base_size = n // 3
    remainder = n % 3
    
    # 分配策略: 多的放前面
    rows = []
    current_idx = 0
    for i in range(3):
        size = base_size + (1 if i < remainder else 0)
        chunk = []
        for j in range(size):
            if current_idx < n:
                item = minum_data[current_idx]
                if isinstance(item, list):
                    chunk.extend(item)
                else:
                    chunk.append(item)
                current_idx += 1
        rows.append(chunk)
        
    return rows

if __name__ == "__main__":
    # 測試 dictionary (6層)
    test_data = [[1],[2],[3],[4],[5],[6]]
    print(f"6層壓縮結果: {distribute_to_three_rows(test_data)}")
    
    # 測試 beautiful (4層)
    test_data_2 = [[1],[2],[3],[4]]
    print(f"4層壓縮結果: {distribute_to_three_rows(test_data_2)}")
