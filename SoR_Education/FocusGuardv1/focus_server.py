"""
Focus Guard 伺服器
提供首頁（介紹與下載點）以及老師控制面板的轉址與服務。
埠號: 5099
"""
import os
from flask import Flask, render_template_string, send_from_directory, send_file

app = Flask(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(SCRIPT_DIR, "downloads")

# 確保下載目錄存在
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 準備 HTML 模板 (首頁)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Focus Guard | 專注力防護系統</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #8b5cf6;
            --primary-hover: #7c3aed;
            --bg: #0f172a;
            --card: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            font-family: 'Inter', 'Noto Sans TC', sans-serif;
            background-color: var(--bg);
            background-image: radial-gradient(at 0% 0%, rgba(139, 92, 246, 0.15) 0, transparent 50%),
                              radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.15) 0, transparent 50%);
            color: var(--text);
            margin: 0; min-height: 100vh;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .container {
            max-width: 800px; padding: 40px; text-align: center;
            background: var(--card); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px; backdrop-filter: blur(12px);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }
        h1 { font-size: 2.5rem; margin-bottom: 10px; font-weight: 800; background: linear-gradient(to right, #a78bfa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p { font-size: 1.1rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 30px; }
        
        .action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }
        
        .card {
            background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.05);
            padding: 30px 20px; border-radius: 16px; transition: transform 0.2s;
        }
        .card:hover { transform: translateY(-5px); border-color: rgba(255,255,255,0.15); }
        .card h2 { font-size: 1.3rem; margin-bottom: 10px; }
        .card p { font-size: 0.95rem; margin-bottom: 20px; }
        
        .btn {
            display: inline-block; padding: 12px 24px; border-radius: 12px;
            font-weight: 600; text-decoration: none; transition: 0.2s;
        }
        .btn-primary { background: var(--primary); color: white; box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4); }
        .btn-primary:hover { background: var(--primary-hover); transform: translateY(-2px); }
        .btn-green { background: #10b981; color: white; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4); }
        .btn-green:hover { background: #059669; transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Focus Guard</h1>
        <p>SoR 專注力防護系統・讓學習更高效<br>學生端自動阻擋分心軟體，老師端即時廣播與獎勵管理。</p>
        
        <div class="action-grid">
            <!-- 學生家長下載 -->
            <div class="card">
                <h2>👧 學生端軟體下載</h2>
                <p>請家長下載後協助安裝於學生的電腦中。上課時輸入「教室代碼」即可連線。</p>
                <a href="/download/mac" class="btn btn-primary">下載 Mac 版本</a>
                <!-- <a href="/download/win" class="btn" style="background:#555; color:white; margin-top:10px;">下載 Windows 版 (暫未提供)</a> -->
            </div>
            
            <!-- 老師面板入口 -->
            <div class="card">
                <h2>👨‍🏫 老師控制面板</h2>
                <p>線上課堂管理、一鍵鎖定分心軟體、發放安迪幣獎勵、即時廣播。</p>
                <a href="/teacher" class="btn btn-green">進入老師控制台</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/manual')
def manual():
    # 讀取根目錄下的 Interactive_User_Guide.html
    manual_path = os.path.join(os.path.dirname(SCRIPT_DIR), 'Interactive_User_Guide.html')
    if os.path.exists(manual_path):
        return send_file(manual_path)
    # 若被放在更上層
    alt_path = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), 'Interactive_User_Guide.html')
    return send_file(alt_path)

@app.route('/teacher')
def teacher_dashboard():
    # 讀取現有老師後台 HTML
    return send_file(os.path.join(SCRIPT_DIR, 'teacher_dashboard.html'))

@app.route('/download/mac')
def download_mac():
    file_path = os.path.join(DOWNLOADS_DIR, 'FocusGuard_Mac.zip')
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name='FocusGuard_Mac.zip')
    return "錯誤：找不到 Mac 安裝檔。請先執行 build_mac.sh 打包並壓縮。", 404

# 如果有需要 serving 其他 assets (例如圖片)
@app.route('/<path:filename>')
def serve_static(filename):
    if filename in ["sor logo.png", "andy_doll.png"]:
        return send_from_directory(SCRIPT_DIR, filename)
    return "Not Found", 404

if __name__ == '__main__':
    print("\n🛡️ Focus Guard 系統啟動中...")
    print("   🌐 Web 伺服器運行於: http://localhost:5099\n")
    app.run(port=5099, debug=False)
