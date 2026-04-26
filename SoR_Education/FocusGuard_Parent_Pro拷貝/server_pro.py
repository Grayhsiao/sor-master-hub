import http.server
import socketserver
import os

PORT = 5100
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # 預設首頁指向 portal_pro.html
        if self.path == '/':
            self.path = '/portal_pro.html'
        return super().do_GET()

if __name__ == "__main__":
    print(f"🚀 Focus Pro 家長門戶伺服器已啟動: http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已關閉")
            httpd.shutdown()
