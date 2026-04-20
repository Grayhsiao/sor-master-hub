"""
SoR 知識庫 API 伺服器 v1.0
============================
這是連接 PostgreSQL 資料庫與前端 App / Line Bot / FocusGuard 的核心橋樑。

啟動方式:
  python3 server.py

API 端點:
  GET /api/words?q=bed            → 搜尋單字
  GET /api/words?q=bed&limit=20   → 搜尋單字（限制筆數）
  GET /api/word/bed               → 取得單一單字完整資料
  GET /api/chapters               → 取得 700單章節清單
  GET /api/chapter/1              → 取得某章節的所有單字
  GET /health                     → 伺服器健康狀態
"""

import os
import json
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允許前端跨域存取

# ─── PostgreSQL 連線設定 ──────────────────────────────────────
# 本機開發用
LOCAL_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "sor_education",
    "user": os.environ.get("USER", "gray"),
    "password": ""
}

# 雲端正式機 (77.42.94.7)
CLOUD_DB = {
    "host": "77.42.94.7",
    "port": 5433,
    "dbname": "sor_education",
    "user": "postgres",
    "password": os.environ.get("PG_CLOUD_PASSWORD", "")
}

# 選擇連線目標 (預設本機，設環境變數 USE_CLOUD=1 則連雲端)
DB_CONFIG = CLOUD_DB if os.environ.get("USE_CLOUD") == "1" else LOCAL_DB

# ─── 檔案路徑設定 ──────────────────────────────────────────────
# 指向 700單與音典的資料夾
APP_DIR = os.path.dirname(__file__)
AUDIO_BASE_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "700單", "音檔"))
IMAGE_BASE_DIR = os.path.abspath(os.path.join(APP_DIR, "assets", "images"))

def get_db():
    """建立資料庫連線"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)

# ─── 靜態檔案服務 ──────────────────────────────────────────────

@app.route('/')
def serve_index():
    """回傳主要網頁"""
    return send_from_directory(APP_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """回傳指定路徑的靜態檔案"""
    if os.path.exists(os.path.join(APP_DIR, path)):
        return send_from_directory(APP_DIR, path)
    return "Not Found", 404

@app.route('/assets/images/<path:filename>')
def serve_images(filename):
    """回傳音標圖片"""
    return send_from_directory(IMAGE_BASE_DIR, filename)

@app.route('/api/audio/<path:filename>')
def get_audio_file(filename):
    """回傳音檔"""
    return send_from_directory(AUDIO_BASE_DIR, filename)

# ─── 欄位選取：前端需要的核心欄位 ───────────────────────────────
CORE_FIELDS = """
    sor_id, word, kk, trans_zh, chinese_pub,
    minum, intonation, syllables,
    hc, v_vowel, tc,
    pos_n, pos_v, pos_adj, pos_adv,
    id_700, chapter_700, chapter_name_700, category_700,
    grade_junior, grade_gept,
    audio_file
"""

# ─── API 端點 ──────────────────────────────────────────────────

@app.route('/health')
def health():
    """健康狀態檢查"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM words")
        result = cursor.fetchone()
        conn.close()
        return jsonify({
            "status": "ok",
            "database": DB_CONFIG["host"],
            "total_words": result["total"],
            "message": "SoR 知識庫運作正常 🎉"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/words')
def search_words():
    """
    搜尋單字 API
    參數:
        q       - 搜尋字串 (可部分比對)
        limit   - 回傳筆數上限 (預設 50)
        chapter - 篩選指定章節 (700單章節號)
        grade   - 篩選學習階段 (junior / gept)
    """
    q       = request.args.get('q', '').strip()
    limit   = min(int(request.args.get('limit', 50)), 1000) # 提高上限以支援一次顯示 700單
    chapter = request.args.get('chapter', '')
    grade   = request.args.get('grade', '')
    sort_mode = request.args.get('sort', 'sor')

    where_clauses = []
    params = []

    if q:
        where_clauses.append("(word ILIKE %s OR trans_zh ILIKE %s OR chinese_pub ILIKE %s)")
        params += [f"{q}%", f"%{q}%", f"%{q}%"]

    if chapter:
        where_clauses.append("chapter_700 = %s")
        params.append(chapter)

    # 如果是 700單模式，強制過濾只顯示有 id_700 的單字
    if sort_mode == '700':
        where_clauses.append("(id_700 IS NOT NULL AND id_700 != '')")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # 排序邏輯
    if sort_mode == '700':
        # 依照 700單章節序與單字序排序
        order_sql = "ORDER BY NULLIF(chapter_700, '')::INTEGER, NULLIF(id_700, '')::INTEGER, word"
    else:
        # 依照音典原始 sor_id 排序
        order_sql = "ORDER BY sor_id"

    sql = f"""
        SELECT {CORE_FIELDS}
        FROM words
        {where_sql}
        {order_sql}
        LIMIT %s
    """
    params.append(limit)

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        # 轉換 minum 字串為 JSON
        results = []
        for row in rows:
            item = dict(row)
            # 確保 minum 始終為列表結構
            minum_raw = item.get('minum')
            if isinstance(minum_raw, str) and minum_raw.strip():
                try:
                    item['minum'] = json.loads(minum_raw)
                except:
                    item['minum'] = []
            elif isinstance(minum_raw, list):
                # 已經是 list
                pass
            else:
                item['minum'] = []
            results.append(item)

        return jsonify({
            "query": q,
            "count": len(results),
            "words": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/word/<string:word>')
def get_word(word):
    """取得單一單字的完整資料"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM words WHERE LOWER(word) = LOWER(%s) LIMIT 1",
            (word,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": f"找不到單字: {word}"}), 404

        item = dict(row)
        minum_raw = item.get('minum')
        if isinstance(minum_raw, str) and minum_raw.strip():
            try:
                item['minum'] = json.loads(minum_raw)
            except:
                item['minum'] = []
        elif isinstance(minum_raw, list):
            pass
        else:
            item['minum'] = []

        return jsonify(item)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chapters')
def get_chapters():
    """取得 700單所有章節清單"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chapter_700, chapter_name_700, COUNT(*) as word_count
            FROM words
            WHERE chapter_700 IS NOT NULL
            GROUP BY chapter_700, chapter_name_700
            ORDER BY chapter_700
        """)
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"chapters": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chapter/<string:chapter_id>')
def get_chapter_words(chapter_id):
    """取得某章節的所有單字"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {CORE_FIELDS} FROM words WHERE chapter_700 = %s ORDER BY word",
            (chapter_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            item = dict(row)
            # 確保 minum 始終為列表結構
            minum_raw = item.get('minum')
            if isinstance(minum_raw, str) and minum_raw.strip():
                try:
                    item['minum'] = json.loads(minum_raw)
                except:
                    item['minum'] = []
            elif isinstance(minum_raw, list):
                # 已經是 list
                pass
            else:
                item['minum'] = []
            results.append(item)

        return jsonify({"chapter": chapter_id, "count": len(results), "words": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    db_label = "☁️  雲端 PostgreSQL" if os.environ.get("USE_CLOUD") == "1" else "🏠 本機 PostgreSQL"
    print("=" * 55)
    print("  SoR 知識庫 API 伺服器 v1.0")
    print(f"  資料來源：{db_label} ({DB_CONFIG['host']}:{DB_CONFIG['port']})")
    print("=" * 55)
    print("  API 端點：")
    print("    GET /health")
    print("    GET /api/words?q=<字>")
    print("    GET /api/word/<字>")
    print("    GET /api/chapters")
    print("    GET /api/chapter/<章節號>")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5055, debug=True)
