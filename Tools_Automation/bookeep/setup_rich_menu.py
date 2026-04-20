import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

def setup_rich_menu():
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # 1. 定義圖文選單結構 (1200x810, 4格)
    rich_menu_data = {
        "size": {"width": 1200, "height": 810},
        "selected": True,
        "name": "Bookeep Rich Menu",
        "chatBarText": "快速選單",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 600, "height": 405},
                "action": {"type": "message", "text": "報表"}
            },
            {
                "bounds": {"x": 600, "y": 0, "width": 600, "height": 405},
                "action": {"type": "message", "text": "家庭報表"}
            },
            {
                "bounds": {"x": 0, "y": 405, "width": 600, "height": 405},
                "action": {"type": "message", "text": "查詢ID"}
            },
            {
                "bounds": {"x": 600, "y": 405, "width": 600, "height": 405},
                "action": {"type": "message", "text": "使用教學"}
            }
        ]
    }

    # 2. 建立圖文選單
    print("--- 正在建立圖文選單 ---")
    response = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        headers=headers,
        data=json.dumps(rich_menu_data)
    )
    
    if response.status_code not in [200, 201]:
        print(f"建立失敗: {response.text}")
        return

    rich_menu_id = response.json()['richMenuId']
    print(f"成功！Rich Menu ID: {rich_menu_id}")

    # 3. 上傳圖片
    print("--- 正在上傳選單圖片 ---")
    img_headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'image/png'
    }
    
    with open('assets/rich_menu.png', 'rb') as f:
        img_response = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers=img_headers,
            data=f
        )
    
    if img_response.status_code != 200:
        print(f"圖片上傳失敗: {img_response.text}")
        return
    print("圖片上傳成功！")

    # 4. 設定為預設選單
    print("--- 正在設定為預設選單 ---")
    requests.post(
        f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
        headers=headers
    )
    print("恭喜！圖文選單已成功設定完成！✨")

if __name__ == "__main__":
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("錯誤：找不到 LINE_CHANNEL_ACCESS_TOKEN，請檢查 .env 檔案。")
    else:
        setup_rich_menu()
