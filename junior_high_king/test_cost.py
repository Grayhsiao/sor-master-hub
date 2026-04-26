import sqlite3
import requests
import json
import os

# --- 設定路徑與 API ---
DB_PATH = '/Users/gray/Documents/python_project/junior_high_king/questions.db' # 請根據實際檔名修改
OPENROUTER_API_KEY = "你的_OPENROUTER_API_KEY"

def audit_question_cost():
    # 1. 連接資料庫並抓取一題
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 假設資料表叫 questions，欄位包含 content
    cursor.execute("SELECT content FROM questions LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("資料庫沒東西喔！")
        return

    question_text = row[0]

    # 2. 發送給 OpenRouter 的 MiniMax
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "minimax/minimax-01", 
            "messages": [
                {"role": "system", "content": "你是一個學科難度分析師。請分析題目並給出 L1-L5 難度建議。"},
                {"role": "user", "content": question_text}
            ]
        })
    )

    result = response.json()
    
    # 3. 計算成本
    # 假設 MiniMax-01 價格為 $0.2/1M tokens
    usage = result.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = prompt_tokens + completion_tokens
    
    cost = (total_tokens / 1_000_000) * 0.20

    print(f"--- 測試報告 ---")
    print(f"題目內容片段: {question_text[:30]}...")
    print(f"消耗 Tokens: {total_tokens}")
    print(f"這一題的成本: ${cost:.6f} USD")
    print(f"也就是說，1美金可以處理大約 {int(1/cost)} 題！")

# 執行測試
audit_question_cost()