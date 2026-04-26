import os, requests, json
from dotenv import load_dotenv
load_dotenv('../../.env')
key = os.getenv("GOOGLE_API_KEY")
vid = "myTQtIQ2gDE"
url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,topicDetails&id={vid}&key={key}"
r = requests.get(url)
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
