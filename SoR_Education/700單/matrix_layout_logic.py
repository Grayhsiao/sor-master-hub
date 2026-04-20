import math

def distribute_by_syllables(minum_data, num_syllables):
    """
    根據語調符號的數量 (num_syllables)，對應拆分音標數據。
    minum_data 格式例: [[[1],[59,60]], [[15],[44]], [[4],[43]]]
    """
    if not minum_data or not isinstance(minum_data, list):
        return [[]] * num_syllables
    
    # 原始數據的層級數
    n = len(minum_data)
    
    # 如果層級剛好等於音節數，直接 1:1 對應
    if n == num_syllables:
        return minum_data
    
    # 如果層級較少 (例如 2 層但要求 3 個音節)，則後面補空
    if n < num_syllables:
        return minum_data + [[]] * (num_syllables - n)
        
    # 如果層級較多 (例如 6 層但要求 3 個音節)，則進行合併
    result = []
    base_size = n // num_syllables
    remainder = n % num_syllables
    
    current_idx = 0
    for i in range(num_syllables):
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
        result.append(chunk)
        
    return result

def distribute_to_three_rows(minum_data):
    """
    保留舊版相容性
    """
    return distribute_by_syllables(minum_data, 3)

if __name__ == "__main__":
    # 測試程式
    test_data = [[1, 2], [3], [4], [5]]
    print(f"4層分配給3音節: {distribute_by_syllables(test_data, 3)}")
    print(f"4層分配給2音節: {distribute_by_syllables(test_data, 2)}")
