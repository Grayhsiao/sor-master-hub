import re

class TermCorrector:
    def __init__(self):
        # 強制替換表 (不分語境)
        self.global_replaces = {
            "雙目前": "雙母語",
            "次地": "次第",
            "刺地": "次第",
            "SOR": "SoR",
            "Sor": "SoR",
            "史考特": "蕭博士", # 防止語音轉錄誤判人名
        }
        
        # 語境敏感替換規則 (使用正則運算式)
        self.context_rules = [
            # 1. 音素/音速/因素 的修正
            # 如果出現 PA、覺察、拆解、學習等字眼，音速/因素 通常應為 音素
            (r'(PA|覺察|拆解|學習|辨識|教學|具備|提取)(音速|因素)', r'\1音素'),
            (r'(音速|因素)(覺察|拆解|辨識|學習|教學)', r'音素\1'),
            
            # 2. 次第 的修正
            # 如果出現 學習、教學、順序、拾級而上，次地 應為 次第
            (r'(學習|教學|順序|邏輯|教育)(次地)', r'\1次第'),
            (r'(次地)(分明|井然|有序|顛倒)', r'次第\1'),
        ]
        
        # 保護名單 (絕對不替換)
        self.protected_terms = [
            "超音速",
            "音量音位音速", # 博士定義的五音屬性之一
            "政治因素",
            "環境因素",
        ]

    def correct(self, text):
        if not text:
            return text
            
        # 先處理保護名單 (暫時替換為佔位符)
        placeholders = {}
        for i, term in enumerate(self.protected_terms):
            if term in text:
                token = f"__PROTECTED_{i}__"
                placeholders[token] = term
                text = text.replace(term, token)
        
        # 處理全局替換
        for old, new in self.global_replaces.items():
            text = text.replace(old, new)
            
        # 處理語境規則
        for pattern, replacement in self.context_rules:
            text = re.sub(pattern, replacement, text)
        
        # 特殊修正：處理單獨出現的「音速」若上下文有 SoR 特徵但沒捕捉到
        # 這部分較主觀，暫以強關聯為主
        
        # 還原保護名單
        for token, original in placeholders.items():
            text = text.replace(token, original)
            
        return text

# 測試代碼
if __name__ == "__main__":
    corrector = TermCorrector()
    test_cases = [
        "學好 PA 音速是關鍵",
        "這是一個政治因素",
        "學習次地非常重要",
        "超音速發音法很好用",
        "我們要進行音速覺察訓練",
        "音量音位音速是語音五要素"
    ]
    for case in test_cases:
        print(f"原句: {case} -> 修正: {corrector.correct(case)}")
