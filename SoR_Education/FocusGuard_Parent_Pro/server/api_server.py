import json
from urllib.parse import urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import core.config as config

# 引用 AI 與任務引擎
try:
    import gemini_tutor
    from task_engine import FocusState, DailyTaskManager, WeakPointsManager
except ImportError:
    pass

# 全域參考主程式實例 (由 app.py 啟動時注入)
APP_INSTANCE = None

def set_app_instance(instance):
    global APP_INSTANCE
    APP_INSTANCE = instance

class SoRRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): return # 靜音日誌

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path

        # 靜態頁面服務
        if path == "/" or path == "/parent":
            self.serve_file("control_panel.html")
        elif path == "/student":
            self.serve_file("student_portal.html")
        
        # API 端點
        elif path == "/api/status":
            res = {
                "active": APP_INSTANCE.is_active if APP_INSTANCE else False, 
                "student_id": APP_INSTANCE.student_id if APP_INSTANCE else "PRO-UNKNOWN",
                "cloud_status": APP_INSTANCE.current_remote_status if APP_INSTANCE else "LOCKED"
            }
            self.send_json(res)
        elif path == "/api/update_id":
            pass
        elif path == "/api/tokens":
            try:
                status = FocusState.get_unlock_status()
                self.send_json(status)
            except: self.send_json({})
        elif path == "/api/get_tasks":
            try:
                tasks = DailyTaskManager.get_today_tasks()
                qs = tasks["tasks"]["homework"].get("questions", [])
                self.send_json({"tasks": qs})
            except: self.send_json({"tasks": []})
        elif path == "/api/weak_points":
            try:
                data = WeakPointsManager.get_all_weak_points()
                self.send_json(data)
            except: self.send_json({})
        else:
            self.send_error(404)

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        length = int(self.headers.get('content-length', 0))
        post_data = json.loads(self.rfile.read(length)) if length > 0 else {}

        if path == "/api/generate_questions":
            try:
                qs = gemini_tutor.generate_questions(
                    subject_key=post_data.get("subject_key", "math_7"),
                    difficulty=post_data.get("difficulty", 1),
                    count=post_data.get("count", 5),
                    custom_topic=post_data.get("custom_topic", "")
                )
                if qs.get("questions"):
                    DailyTaskManager.set_homework_config(
                        post_data.get("subject_key"), 
                        qs["questions"], 
                        post_data.get("difficulty")
                    )
                    self.send_json({"ok": True, "data": qs})
                else:
                    self.send_json({"ok": False, "msg": "AI 出題失敗"})
            except: self.send_json({"ok": False})

        elif path == "/api/grade_text":
            try:
                res = gemini_tutor.grade_answer_text(
                    student_answer=post_data.get("student_answer", ""),
                    question=post_data.get("question", ""),
                    correct_answer=post_data.get("correct_answer", ""),
                    key_steps=post_data.get("key_steps", []),
                    attempt_count=post_data.get("attempt_count", 1)
                )
                DailyTaskManager.submit_answer("homework", post_data.get("question_id"), res)
                self.send_json(res)
            except: self.send_json({"ok": False})

        elif path == "/api/grade_photo":
            try:
                res = gemini_tutor.grade_answer(
                    image_base64=post_data.get("image_base64", ""),
                    question=post_data.get("question", ""),
                    correct_answer=post_data.get("correct_answer", ""),
                    key_steps=post_data.get("key_steps", []),
                    attempt_count=post_data.get("attempt_count", 1)
                )
                DailyTaskManager.submit_answer("homework", post_data.get("question_id"), res)
                self.send_json(res)
            except: self.send_json({"ok": False})

        elif path == "/api/get_explanation":
            try:
                res = gemini_tutor.generate_explanation(
                    question=post_data.get("question", ""),
                    correct_answer=post_data.get("correct_answer", ""),
                    key_steps=post_data.get("key_steps", [])
                )
                self.send_json(res)
            except: self.send_json({"ok": False})

        elif path == "/api/redeem_token":
            try:
                res = FocusState.redeem_token()
                self.send_json(res)
            except: self.send_json({"ok": False})
            
        elif path == "/api/add_token":
            if post_data.get("pin") == "1234":
                try:
                    FocusState.add_tokens(1, "家長獎勵")
                    self.send_json({"ok": True})
                except: self.send_json({"ok": False})
            else:
                self.send_json({"ok": False, "msg": "PIN 錯誤"})
        
        elif path == "/api/start":
            if APP_INSTANCE: APP_INSTANCE.is_active = True
            self.send_json({"ok": True})
        
        elif path == "/api/stop":
            if post_data.get("pin") == "1234":
                if APP_INSTANCE: APP_INSTANCE.is_active = False
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False})
        
        elif path == "/api/update_id":
            new_id = post_data.get("student_id")
            if new_id and APP_INSTANCE:
                APP_INSTANCE.student_id = new_id
                with open(config.CONFIG_FILE, "w") as f:
                    json.dump({"student_id": new_id}, f)
                self.send_json({"ok": True, "student_id": new_id})
            else:
                self.send_json({"ok": False, "msg": "無效的 ID"})

    def serve_file(self, filename):
        try:
            path = config.resource_path(filename)
            with open(path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
        except:
            self.send_error(404)

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run_api_server():
    server = HTTPServer(('localhost', 5200), SoRRequestHandler)
    print("🌍 SoR API Server 啟動於 http://localhost:5200")
    server.serve_forever()
