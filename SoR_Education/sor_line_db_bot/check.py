import google.generativeai as genai

# 請填入你的 Google API Key
GOOGLE_API_KEY = 'AIzaSyBO5NMLxYBpjoENXc2Bx0wBp6ucu3Hciqo'

genai.configure(api_key=GOOGLE_API_KEY)

print("正在查詢可用模型...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 發現模型: {m.name}")
except Exception as e:
    print(f"查詢失敗: {e}")