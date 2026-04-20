from gemini_manager import GeminiManager
import os

def test_gemini_parsing():
    print("🚀 開始測試 Gemini 解析功能...")
    gm = GeminiManager()
    
    # 測試文字解析
    print("\n--- 測試 1: 文字解析 ---")
    text_result = gm.parse_bookkeeping_content(text_content="今天午餐花了 150 元，很好吃")
    print(f"結果: {text_result}")
    
    if text_result and text_result.get('amount') == 150:
        print("✅ 文字解析測試通過！")
    else:
        print("❌ 文字解析測試失敗。")

if __name__ == "__main__":
    test_gemini_parsing()
