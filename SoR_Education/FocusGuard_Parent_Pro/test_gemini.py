import os, requests
from dotenv import load_dotenv
load_dotenv('../../.env')
key = os.getenv("GOOGLE_API_KEY")
title = "Unknown Video Title"
url = "https://www.youtube.com/watch?v=myTQtIQ2gDE&list=RDmyTQtIQ2gDE&start_radio=1"
payload = {"contents": [{"parts": [{"text": f"判斷此內容為 learning 或 entertainment (僅回傳單字): {title} {url}"}]}]}
url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
r = requests.post(url_api, json=payload)
print(r.json()['candidates'][0]['content']['parts'][0]['text'])
