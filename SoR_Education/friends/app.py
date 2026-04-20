from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'friends_scripts.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # 讀取所有角色資訊
    conn = get_db()
    characters = conn.execute('SELECT * FROM character_registry').fetchall()
    conn.close()
    return render_template('index.html', characters=characters)

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    speaker = request.args.get('speaker', '').strip()
    season = request.args.get('season', '').strip()
    episode = request.args.get('episode', '').strip()
    
    conn = get_db()
    # Join with character_registry to get speaker descriptions, traits and avatar
    query = '''
        SELECT s.season, s.episode, s.line_index, s.speaker, s.line, 
               s.theme, s.tone, s.action_instruction, s.chinese_line, s.literal_translation, s.start_time,
               c.description as char_desc, c.traits, c.avatar
        FROM scripts s
        LEFT JOIN character_registry c ON s.speaker = c.name
        WHERE 1=1
    '''
    params = []
    
    if keyword:
        query += ' AND s.line LIKE ?'
        params.append(f'%{keyword}%')
    if speaker:
        query += ' AND s.speaker = ?'
        params.append(speaker)
    if season:
        query += ' AND s.season = ?'
        params.append(season)
    if episode:
        query += ' AND s.episode = ?'
        params.append(episode)
    
    # 如果沒有關鍵字，則隨機抽取高分金句；如果有關鍵字，則權重優先
    if not keyword:
        query += ' ORDER BY s.priority_score DESC, RANDOM()'
    else:
        query += ' ORDER BY s.priority_score DESC, s.season ASC, s.episode ASC'
    
    query += ' LIMIT 40'
    results = conn.execute(query, params).fetchall()
    
    search_results = []
    for row in results:
        s, e, idx = row['season'], row['episode'], row['line_index']
        context = conn.execute('''
            SELECT speaker, line, chinese_line 
            FROM scripts 
            WHERE season=? AND episode=? AND line_index BETWEEN ? AND ?
            ORDER BY line_index ASC
        ''', (s, e, idx-3, idx+3)).fetchall()
        
        formatted_context = []
        for c in context:
            # 標註目標台詞
            prefix = f"[{c['speaker']}]:" if (c['line'] == row['line'] and c['speaker'] == row['speaker']) else f"{c['speaker']}:"
            line_str = f"{prefix} {c['line']}"
            if c['chinese_line']:
                line_str += f"\n   ({c['chinese_line']})"
            formatted_context.append(line_str)
            
        search_results.append({
            'season': s,
            'episode': e,
            'speaker': row['speaker'],
            'line': row['line'],
            'char_desc': row['char_desc'] or '主要角色',
            'theme': row['theme'] or 'General',
            'tone': row['tone'] or 'Normal',
            'action': row['action_instruction'] or 'No specific action',
            'chinese_line': row['chinese_line'],
            'literal_translation': row['literal_translation'],
            'start_time': row['start_time'] or '00:00:00.000',
            'context': '\n'.join(formatted_context),
            'persona_tags': row['traits'] or '影集靈魂',
            'avatar': row['avatar'] or '/static/img/default.png'
        })
        
    conn.close()
    return jsonify(search_results)

@app.route('/vocabulary')
def vocabulary_hub():
    conn = get_db()
    # 從 lexicon 表獲取所有唯一分類
    categories = conn.execute('SELECT DISTINCT category FROM lexicon WHERE category IS NOT NULL AND category != ""').fetchall()
    conn.close()
    return render_template('vocabulary.html', themes=[c['category'] for c in categories])

@app.route('/api/vocabulary/words')
def get_vocab_words():
    category = request.args.get('theme', '')
    conn = get_db()
    if category:
        results = conn.execute('SELECT word, category FROM lexicon WHERE category = ?', (category,)).fetchall()
    else:
        results = conn.execute('SELECT word, category FROM lexicon LIMIT 200').fetchall()
    conn.close()
    
    return jsonify([{'word': r['word'].capitalize(), 'theme': r['category']} for r in results])

@app.route('/api/vocabulary/examples')
def get_vocab_examples():
    word = request.args.get('word', '').lower()
    conn = get_db()
    # 為該單字挑選權重最高且具備時間戳記的 3 個例句
    examples = conn.execute('''
        SELECT speaker, season, episode, line, chinese_line, start_time, end_time 
        FROM scripts 
        WHERE LOWER(line) LIKE ? 
        ORDER BY priority_score DESC, (start_time IS NOT NULL) DESC 
        LIMIT 3
    ''', (f'%{word}%',)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in examples])

if __name__ == '__main__':
    app.run(debug=True, port=5001)
