import pandas as pd
import os

EXCEL_FILE = "700單_量產清單.xlsx"

# 準備填充內容 (範例 5 個字)
# 700Id: 27(I), 28(you), 38(friend), 40(boy), 41(girl)
updates = {
    "I": {
        "Order": "word ph chinese sent1 extra1",
        "Sentence1": "I'm game! (我很有興趣！)",
        "Sentence2": "I am Iron Man. (我是鋼鐵人)",
        "Extra": "鋼鐵人經典名言，展現自信與力量。"
    },
    "you": {
        "Order": "word ph chinese sent1 extra1",
        "Sentence1": "You bet! (那是當然的！)",
        "Sentence2": "You are my sunshine. (你是我的陽光)",
        "Extra": "經典暖心名曲，適合教導人與人的連結。"
    },
    "friend": {
        "Order": "word ph chinese sent1 extra1",
        "Sentence1": "She has my back. (她很挺我。)",
        "Sentence2": "You've got a friend in me. (你有我這個朋友)",
        "Extra": "《玩具總動員》主題曲，經典中的經典。"
    },
    "boy": {
        "Order": "word ph chinese sent1 extra1",
        "Sentence1": "Oh boy! (天哪！/哇！)",
        "Sentence2": "He is a lost boy. (他是個迷失的孩子)",
        "Extra": "連結小飛俠 Peter Pan，象徵冒險與純真。"
    },
    "girl": {
        "Order": "word ph chinese sent1 extra1",
        "Sentence1": "That's my girl! (做的好！/真不愧是我心目中的女孩)",
        "Sentence2": "Girls just want to have fun. (女孩們只想玩樂)",
        "Extra": "80年代活力金曲，代表自由與快樂。"
    }
}

def fill_excel():
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ 找不到檔案: {EXCEL_FILE}")
        return

    df = pd.read_excel(EXCEL_FILE)
    
    # 執行更新
    for word, content in updates.items():
        mask = df['word'] == word
        if mask.any():
            df.loc[mask, 'Order'] = content['Order']
            df.loc[mask, 'Sentence1'] = content['Sentence1']
            df.loc[mask, 'Sentence2'] = content['Sentence2']
            print(f"✅ 已填充單字: {word}")

    df.to_excel(EXCEL_FILE, index=False)
    print(f"🚀 Excel 更新完成！")

if __name__ == "__main__":
    fill_excel()
