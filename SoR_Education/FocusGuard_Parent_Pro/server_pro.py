import http.server
import socketserver
import os
import json
import urllib.parse

PORT = 5100
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(DIRECTORY, "guard_status.json")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        # 1. 預設首頁指向 portal_pro.html
        if parsed_path.path == '/':
            self.path = '/portal_pro.html'
            return super().do_GET()
            
        # 2. 獲取狀態 API: /get_status?id=PRO1234
        if parsed_path.path == '/get_status':
            params = urllib.parse.parse_qs(parsed_path.query)
            target_id = params.get('id', [None])[0]
            
            if not target_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing ID')
                return

            status_data = {}
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r") as f:
                    status_data = json.load(f)
            
            # 回傳該 ID 的狀態，若無則回傳預設解鎖狀態
            result = status_data.get(target_id, {"status": "UNLOCKED"})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # 允許跨域
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            return

        return super().do_GET()

    def do_POST(self):
        # 3. 設定狀態 API: /set_status
        if self.path == '/set_status':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            target_id = data.get('id')
            new_status = data.get('status')
            
            if not target_id or not new_status:
                self.send_response(400)
                self.end_headers()
                return

            # 讀取現有狀態並更新
            status_data = {}
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r") as f:
                    status_data = json.load(f)
            
            status_data[target_id] = {
                "status": new_status,
                "update_at": data.get("update_at", 0)
            }
            
            with open(STATUS_FILE, "w") as f:
                json.dump(status_data, f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"result": "OK"}).encode())
            return

    def do_OPTIONS(self):
        # 處理 CORS 預檢請求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == "__main__":
    print(f"🚀 Focus Pro 雲端通訊中心已啟動: http://0.0.0.0:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已關閉")
            httpd.shutdown()
