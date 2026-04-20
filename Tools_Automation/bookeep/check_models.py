import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    try:
        print("可用模型列表：")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    list_models()
