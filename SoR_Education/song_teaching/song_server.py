"""
SoR 英文歌詞教材系統 — Flask 後端伺服器
執行: python3 song_server.py
瀏覽: http://localhost:5088
"""
import os, sys, re, json, time, hashlib, threading, platform, random, requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file

app = Flask(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSHEETS_DIR = os.path.join(SCRIPT_DIR, "worksheets")
INDEX_JSON = os.path.join(SCRIPT_DIR, "worksheets.json")
os.makedirs(WORKSHEETS_DIR, exist_ok=True)

# ── 狀態追蹤（簡單的進度管理）────────────────────────────────────────────────
progress_store = {}  # job_id → {'status': 'running'|'done'|'error', 'log': [...]}

def update_progress(job_id, msg, status="running"):
    if job_id not in progress_store:
        progress_store[job_id] = {'status': 'running', 'log': [], 'file': None}
    progress_store[job_id]['log'].append(msg)
    progress_store[job_id]['status'] = status
    print(f"[{job_id[:6]}] {msg}")

# ── 歷史紀錄 ─────────────────────────────────────────────────────────────────
def load_index():
    if os.path.exists(INDEX_JSON):
        with open(INDEX_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_to_index(entry):
    records = load_index()
    records.insert(0, entry)
    with open(INDEX_JSON, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# ── 路由：靜態頁面 ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_file(os.path.join(SCRIPT_DIR, 'song_index.html'))

@app.route('/worksheets/<path:filename>')
def serve_worksheet(filename):
    return send_from_directory(WORKSHEETS_DIR, filename)

# ── 路由：進度查詢 ────────────────────────────────────────────────────────────
@app.route('/progress/<job_id>')
def get_progress(job_id):
    data = progress_store.get(job_id, {'status': 'not_found', 'log': []})
    return jsonify(data)

# ── 路由：歷史紀錄 ────────────────────────────────────────────────────────────
@app.route('/api/worksheets')
def list_worksheets():
    return jsonify(load_index())

# ── 路由：刪除 ────────────────────────────────────────────────────────────────
@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_worksheet(filename):
    path = os.path.join(WORKSHEETS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    records = [r for r in load_index() if r.get('file') != filename]
    with open(INDEX_JSON, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})

# ── 路由：生成 ────────────────────────────────────────────────────────────────
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json or {}
    song = data.get('song', '').strip()
    artist = data.get('artist', '').strip()
    if not song:
        return jsonify({'error': '請輸入歌名'}), 400

    job_id = hashlib.md5(f"{song}{artist}{time.time()}".encode()).hexdigest()[:12]
    progress_store[job_id] = {'status': 'running', 'log': [], 'file': None}

    def run():
        try:
            from generator import generate_worksheet
            file_name = generate_worksheet(song, artist, WORKSHEETS_DIR, job_id, update_progress)
            if file_name:
                safe_title = re.sub(r'[^\w\s-]', '', song).strip()
                entry = {
                    'title': song,
                    'artist': artist or 'Unknown',
                    'file': file_name,
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
                }
                save_to_index(entry)
                progress_store[job_id]['status'] = 'done'
                progress_store[job_id]['file'] = file_name
            else:
                progress_store[job_id]['status'] = 'error'
        except Exception as e:
            progress_store[job_id]['status'] = 'error'
            progress_store[job_id]['log'].append(f"❌ 錯誤：{e}")
            import traceback; traceback.print_exc()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return jsonify({'job_id': job_id})

if __name__ == '__main__':
    print("\n🎵 SoR 英文歌詞教材系統啟動中...")
    print("   開啟瀏覽器：http://localhost:5088\n")
    app.run(port=5088, debug=False)
