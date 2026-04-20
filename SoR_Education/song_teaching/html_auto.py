"""
=============================================================================
=============================================================================
🎵 Gray 的英文歌詞教材生成器 (V67 Traditional Chinese + Table Word Bank)
=============================================================================
【本次修正：繁體化修復與單字庫表格化 (V67 Update)】
1. 🇹🇼 繁體修復：嚴格鎖定台灣繁體中文，徹底排除簡體字。
2. 📊 單字庫表格化：單字庫 (Word Bank) 改為表格架構，含音標空欄與字義。
3. 📉 標籤精簡：移除 CEFR 單字難度標籤 (A1-C2)。
4. 🎨 視覺延續：保留 V65 美化卡片與多媒體 QR Code 功能。
5. 🛡️ 去重核心：維持 V62 全球與段落內去重邏輯。

【執行前檢查】
需安裝 google-genai
=============================================================================
"""

import os
import sys
import platform
import time
import random
import re 
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("\n❌ 錯誤：找不到 `google-genai` 套件。請執行 pip3 install google-genai")
    sys.exit(1)

# ==========================================
# 🔑 API Key (從環境變數讀取)
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ 錯誤：找不到環境變數 `GEMINI_API_KEY`。")
    print("   請執行：export GEMINI_API_KEY='your_key_here'")
    sys.exit(1)
# ==========================================

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"❌ API Key 設定錯誤: {e}")
    sys.exit(1)

script_dir = os.path.dirname(os.path.abspath(__file__))
CURRENT_MODEL = None

# ---------------------------------------------------------
# 🛠️ 工具函式
# ---------------------------------------------------------
def print_status(message):
    print(f"⚙️  {message}")
    sys.stdout.flush()

def countdown(seconds):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r⏳ 配合 API 流量限制，休息中... {i} 秒   ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r🚀 休息結束，繼續執行！                     \n")
    sys.stdout.flush()

def get_random_headers():
    user_agents = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36']
    return {'User-Agent': random.choice(user_agents), 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Referer': 'https://www.google.com/'}

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# ---------------------------------------------------------
# 🧪 模型設定
# ---------------------------------------------------------
def setup_model():
    global CURRENT_MODEL
    print_status("正在掃描可用模型...")
    try:
        all_models = list(client.models.list())
        chosen = None
        # V59.3 模型優先順序調整：避免選到實驗性模型 (如 2.0-flash 限額較低)
        preferred_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
        
        # 1. 先找 Preferred
        for p in preferred_models:
             for m in all_models:
                m_name = m.name if hasattr(m, 'name') else str(m)
                if p in m_name:
                    chosen = m_name
                    break
             if chosen: break
        
        # 2. 沒找到，才用廣泛搜尋
        if not chosen:
            for m in all_models:
                m_name = m.name if hasattr(m, 'name') else str(m)
                if "flash" in m_name.lower():
                    chosen = m_name; break
        
        if not chosen:
             for m in all_models:
                m_name = m.name if hasattr(m, 'name') else str(m)
                if "pro" in m_name.lower():
                    chosen = m_name; break
        
        if not chosen and all_models:
             chosen = all_models[0].name if hasattr(all_models[0], 'name') else str(all_models[0])

        if not chosen:
            print("❌ 找不到任何可用模型。")
            sys.exit(1)

        CURRENT_MODEL = chosen
        print(f"✅ 鎖定模型：【 {CURRENT_MODEL} 】")
        print("   👉 戰術：[字典定義 + 短句過濾] (內容精準化)")

    except Exception as e:
        print(f"❌ 模型掃描失敗: {e}")
        sys.exit(1)

# ---------------------------------------------------------
# 🧹 歌詞處理 (V58: 增加長度過濾)
# ---------------------------------------------------------
def clean_lyrics_text(text):
    if not text: return ""
    match = re.search(r'\[(Intro|Verse|Chorus|Pre-Chorus|Bridge|Hook)', text, re.IGNORECASE)
    if match: text = text[match.start():]
    else:
        lyrics_marker = re.search(r'Lyrics\s*\n', text)
        if lyrics_marker: text = text[lyrics_marker.end():]
    lines = text.split('\n')
    cleaned = []
    garbage = ["Deutsch", "Français", "Español", "Português", "Svenska", "Italiano"]
    for line in lines:
        line = line.strip()
        if not line: continue
        if sum(1 for g in garbage if g in line) >= 2: continue
        if any(x in line for x in ["Contributors", "Translations", "You might also like", "See more", "Embed"]): continue
        if re.search(r'\[.*Lyrics.*\]', line): continue 
        cleaned.append(line)
    return "\n".join(cleaned)

def is_noise_line(line):
    noise_words = {'oh', 'ah', 'ooh', 'woah', 'yeah', 'hey', 'la', 'da', 'na', 'mmm', 'hmm', 'uh', 'huh', 'ooh-woah', 'oh-oh', 'ah-ah', 'ooh-ooh'}
    clean = re.sub(r'[^\w\s-]', '', line.lower()).strip()
    if not clean: return True 
    if line.startswith('[') and line.endswith(']'): return True 
    
    words = clean.split()
    if all(w in noise_words for w in words): return True 
    
    # === V59.1 修改：過濾掉 4 個字(含)以下的短句 ===
    # User: "四個字以下的不要出現"
    if len(words) <= 4: 
        return True 
        
    return False

def clean_stanza_content(stanza_text):
    """
    清洗段落內容：
    1. 移除噪音行 (Oh, woah...)
    2. 移除短句 (<= 4 words)
    3. 重新組合
    """
    lines = stanza_text.split('\n')
    cleaned_lines = []
    for line in lines:
        if not is_noise_line(line):
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def split_text_into_stanzas(full_text):
    """
    V59: 將歌詞依照雙換行分割成段落 (Stanza)，若無法分割則依照每 6 行切分。
    """
    if "\n\n" in full_text:
        return [s.strip() for s in full_text.split("\n\n") if s.strip()]
    
    # Fallback
    lines = [l for l in full_text.split("\n") if l.strip()]
    return ["\n".join(lines[i:i+6]) for i in range(0, len(lines), 6)]

def is_duplicate_stanza(candidate_stanza, seen_first_lines, is_outro=False):
    """
    V59 核心去重邏輯：檢查該段落的「第一句」是否已出現過。
    Outro 不受限制 (通常比較短或重複，要保留)。
    """
    if is_outro: return False
    
    lines = candidate_stanza.split('\n')
    if not lines: return True # Empty is duplicate/skip
    
    first_line = clean_line_for_comparison(lines[0])
    
    # 檢查是否過短 (小於 10 字元可能是 'Chorus' 標題殘留，但我們已 clean 過，這裡保險)
    if len(first_line) < 5: return False 

    # 檢查是否在已看過的集合中
    for seen in seen_first_lines:
        if similar(first_line, seen) > 0.85: # 高相似度
            print(f"   ✂️ 跳過重複段落 (First Line: {lines[0][:20]}...)")
            return True
            
    return False

def clean_line_for_comparison(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def split_into_batches(lines_list, batch_size=5): 
    return [lines_list[i:i + batch_size] for i in range(0, len(lines_list), batch_size)]

# ---------------------------------------------------------
# V61+V62 核心去重邏輯
# ---------------------------------------------------------
def is_deep_duplicate(new_norm, seen_set):
    """
    V61 Enhanced Check:
    1. Similarity > 0.8
    2. Containment (one inside another, min length > 10)
    3. Jaccard (Words Overlap) > 0.8
    """
    if not new_norm: return True # Empty
    
    new_words = set(new_norm.split())
    if not new_words: return True

    for seen in seen_set:
        # 1. Similarity (SequenceMatcher)
        if similar(new_norm, seen) > 0.8:
             return True
             
        # 2. Containment (避免單字誤判，限制長度 > 10)
        if len(seen) > 10 and len(new_norm) > 10:
             if seen in new_norm or new_norm in seen:
                 return True

        # 3. Word Overlap (Jaccard Index)
        seen_words = set(seen.split())
        if not seen_words: continue
        
        intersection = len(new_words.intersection(seen_words))
        union = len(new_words.union(seen_words))
        
        if union > 0 and (intersection / union) > 0.8:
             return True
             
    return False

# ---------------------------------------------------------
# 🕸️ 爬蟲
# ---------------------------------------------------------
def search_genius(song, artist=""):
    print_status(f"嘗試使用 [Genius] 搜尋...")
    try:
        res = requests.get("https://genius.com/api/search/multi", params={'per_page': 5, 'q': f"{song} {artist}"}, headers=get_random_headers(), timeout=10).json()
        hits = res['response']['sections'][0]['hits']
        for hit in hits:
            if 'result' not in hit: continue
            r = hit['result']
            artist_name = r.get('primary_artist', {}).get('name', 'Unknown')
            if artist and (artist.lower() not in artist_name.lower()) and (similar(artist.lower(), artist_name.lower()) < 0.5): continue
            print(f"   ✅ Genius 鎖定：{r['title']} by {artist_name}")
            return download_genius_lyrics(r['path']), r['title'], artist_name
    except: pass
    return None, None, None

def download_genius_lyrics(path):
    try:
        page = requests.get(f"https://genius.com{path}", headers=get_random_headers(), timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        divs = soup.find_all('div', attrs={'data-lyrics-container': 'true'})
        raw = "\n".join([d.get_text(separator="\n") for d in divs]) if divs else soup.find('div', class_='lyrics').get_text()
        return clean_lyrics_text(raw)
    except: return None

def search_azlyrics(song, artist):
    print_status(f"嘗試切換至 [AZLyrics] 搜尋...")
    try:
        res = requests.get("https://search.azlyrics.com/search.php", params={'q': f"{song} {artist}"}, headers=get_random_headers(), timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if '/lyrics/' in a['href']]
        if not links: return None, None, None
        print(f"   🔗 發現連結，下載中...")
        page = requests.get(links[0], headers=get_random_headers(), timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        div = soup.find('div', class_='col-xs-12 col-lg-8 text-center')
        if div:
            for d in div.find_all('div', recursive=False):
                if not d.attrs: return clean_lyrics_text(d.get_text()), song, artist
    except: pass
    return None, None, None

# ---------------------------------------------------------
# HTML 樣式 (V63: 桌遊與專家版)
# ---------------------------------------------------------
HTML_HEADER = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎵 Master Song Worksheet V67</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&family=ZCOOL+XiaoWei&family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
<style>
    :root {
        --primary-color: #4a90e2;
        --secondary-color: #f39c12;
        --accent-color: #e74c3c;
        --bg-color: #f4f7f6;
        --card-bg: #ffffff;
        --text-color: #2c3e50;
        --border-radius: 12px;
        --shadow: 0 10px 20px rgba(0,0,0,0.08);
    }

    @page { size: A4 portrait; margin: 1cm; }
    
    body { 
        font-family: 'Poppins', 'Noto Sans TC', sans-serif; 
        background: var(--bg-color); 
        color: var(--text-color); 
        margin: 0; 
        padding: 20px;
        line-height: 1.6;
    }

    /* 頂部橫幅：桌遊感 */
    .expert-banner {
        background: linear-gradient(135deg, #2c3e50, #4a90e2);
        color: white;
        padding: 20px;
        border-radius: var(--border-radius);
        text-align: center;
        margin-bottom: 30px;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    .expert-banner h1 { margin: 0; font-size: 2.2em; font-weight: 800; }
    .expert-banner .version-tag {
        position: absolute; top: 10px; right: 10px;
        background: var(--secondary-color);
        padding: 5px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold;
    }

    /* 故事區塊：卡片式設計 */
    .story-box { 
        background: var(--card-bg); 
        border-left: 8px solid var(--primary-color);
        border-radius: var(--border-radius); 
        padding: 25px; 
        margin-bottom: 30px;
        box-shadow: var(--shadow);
    }
    .story-title { font-size: 1.5em; font-weight: bold; color: var(--primary-color); margin-bottom: 15px; display: flex; align-items: center; }
    .story-title::before { content: "📖"; margin-right: 10px; }
    .story-content { font-family: 'Noto Sans TC', serif; font-size: 1.1em; color: #555; }

    /* 歌詞總覽 */
    .lyrics-box { 
        background: #fdfdfd; 
        border: 2px dashed #cbd5e0;
        border-radius: var(--border-radius);
        padding: 30px;
        margin: 30px auto;
        max-width: 800px;
        text-align: center;
    }
    .lyrics-content { 
        font-family: 'Monaco', 'Menlo', monospace; 
        white-space: pre-wrap; 
        font-size: 1.1em; 
        color: #444; 
    }

    /* 教學卡片：核心優化 */
    .teaching-box { 
        page-break-inside: avoid;
        background: var(--card-bg);
        border-radius: var(--border-radius);
        margin-bottom: 40px;
        padding: 30px;
        box-shadow: var(--shadow);
        border: 1px solid #eee;
    }
    .lyric-header { 
        font-size: 1.8em; 
        font-weight: 800; 
        color: #d35400; 
        margin-bottom: 20px;
        border-bottom: 3px solid #f1c40f;
        padding-bottom: 10px;
        font-family: 'Poppins', sans-serif;
    }

    /* 單字標籤 (CEFR) - 小巧美觀 */
    /* .cefr-tag {
        font-size: 0.6em;
        background: #27ae60;
        color: white;
        padding: 1px 4px;
        border-radius: 3px;
        margin-left: 5px;
        vertical-align: middle;
        opacity: 0.8;
    } */

    /* 單字桌：恢復 V59 欄位 (音標欄) */
    .table-container { margin-bottom: 20px; }
    table.word-table { width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; border: 1px solid #ddd; }
    table.word-table th { background: #f8f9fa; padding: 10px; font-size: 0.85em; width: 100px; border-bottom: 1px solid #eee; font-weight: bold; }
    table.word-table td { padding: 12px; border-bottom: 1px solid #eee; text-align: center; }
    table.word-table td.english { font-weight: 800; font-size: 1.4em; color: var(--primary-color); background-color: #fdfdfe; }
    table.word-table td.phonics { height: 40px; background-color: #f0f0f0; border: 1px dashed #ccc; } 
    table.word-table td.chinese { font-family: 'Noto Sans TC', sans-serif; font-size: 1.05em; color: #555; background-color: #f9f9f9; }

    /* 恢復 V59 經典區塊樣式 (單字庫) */
    .word-bank { 
        margin-top: 20px; 
        border: 1px dashed #aaa; 
        padding: 12px; 
        background: #fff; 
        border-radius: 6px;
        font-size: 0.95em;
        color: #444;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* 遊戲化元素：星級獎勵 */
    .xp-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px solid #eee;
    }
    .stars { color: #f1c40f; font-size: 1.5em; letter-spacing: 5px; cursor: pointer; }
    .xp-points { 
        background: #27ae60; color: white; padding: 5px 15px; border-radius: 15px; font-weight: bold; font-size: 0.9em;
    }

    .section-label { font-weight: 800; margin-top: 20px; display: inline-block; background: var(--text-color); color: #fff; padding: 6px 15px; border-radius: 5px; font-size: 0.9em; margin-bottom: 10px; }
    .underline-space { border-bottom: 2px solid #ccc; width: 100%; height: 40px; margin-bottom: 20px; }
    
    .sub-practice { background: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #eee; }
    .sub-line { border-bottom: 1px solid #999; width: 70%; display: inline-block; height: 25px; margin-left: 10px; }

    /* 列印優化 */
    @media print { 
        body { background: white; padding: 0; }
        .teaching-box { box-shadow: none; border: 2px solid #eee; break-inside: avoid; }
        .expert-banner { background: white !important; color: black !important; border: 2px solid black; }
    }
</style>
</head>
<body>
<div class="no-print expert-banner">
    <div class="version-tag">EXPERT V67</div>
    <h1>🎵 Song Learning Adventure</h1>
    <p>Music | Phonics | Games | Achievement</p>
</div>
"""
HTML_FOOTER = """
<script>
    function toggleTask(btn) {
        const content = btn.nextElementSibling;
        content.classList.toggle('show');
        btn.innerText = content.classList.contains('show') ? '🔒 Lock Quest' : '🔑 Unlock Quest';
    }
    
    // 遊戲化互動：點擊星星評分
    document.querySelectorAll('.stars').forEach(starBox => {
        starBox.addEventListener('click', function() {
            let current = this.innerText;
            if (current === '☆☆☆☆☆') this.innerText = '★☆☆☆☆';
            else if (current === '★☆☆☆☆') this.innerText = '★★☆☆☆';
            else if (current === '★★☆☆☆') this.innerText = '★★★☆☆';
            else if (current === '★★★☆☆') this.innerText = '★★★★☆';
            else if (current === '★★★★☆') this.innerText = '★★★★★';
            else this.innerText = '☆☆☆☆☆';
            this.style.color = (this.innerText.includes('★')) ? '#f1c40f' : '#ccc';
        });
    });
</script>
</body></html>"""

# ---------------------------------------------------------
# 核心生成
# ---------------------------------------------------------
def call_gemini_retry(prompt_text):
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=CURRENT_MODEL,
                contents=prompt_text,
                config=types.GenerateContentConfig(temperature=0.1, top_p=1, top_k=32, max_output_tokens=8192)
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err or "exhausted" in err:
                wait = 60 + (attempt * 20)
                print(f"   🛑 流量限制 (429)，休息 {wait} 秒... ({attempt+1}/5)")
                countdown(wait)
            else:
                print(f"   ❌ API 錯誤: {e}")
                time.sleep(5)
    return ""

def generate_intro_part(title, artist, full_lyrics):
    print_status("📝 步驟 A: 生成故事與歌詞 (V64 數位整合)...")
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://www.youtube.com/results?search_query={title}+{artist}+lyrics"
    
    prompt = f"""
    Role: Creative Writing Expert & Music Historian.
    Task: Generate HTML for song intro. Include a QR Code placeholder.
    1. <h1>{title} by {artist}</h1>
    2. <div class="qr-container">
         <img src="{qr_url}" class="qr-code">
         <div class="qr-label">Scan to Play</div>
       </div>
    3. <div class="story-box">
         <div class="story-title">Song Story / Background</div>
         <div class="story-content">(A fascinating, educational background story about this song in Traditional Chinese Taiwan)</div>
       </div>
    4. <div class="lyrics-box">
         <div class="lyrics-content">{full_lyrics}</div>
       </div>
    
    Song: {title} by {artist}
    OUTPUT HTML ONLY. NO OTHER TEXT.
    """
    return call_gemini_retry(prompt)

def generate_teaching_batch(batch_lines):
    # V67: 繁體修復 + 單字庫表格化 + 移除 CEFR
    prompt = f"""
    Role: Senior English Teacher (Taiwan).
    Task: Create HTML Teaching Boxes for these specific lines. 
    LANGUAGE: USE TRADITIONAL CHINESE (TAIWAN) ONLY. NO SIMPLIFIED CHINESE.
    
    LINES TO TEACH:
    {batch_lines}

    *** KEY RULES ***
    1. WORD TABLE: For each word, provide English, a completely EMPTY Phonics row, and a Chinese Dictionary Definition (Traditional Chinese, max 2 meanings). NO CEFR TAGS.
    2. TRANSLATION: "自己翻 (Translate)" followed by a long underline space.
    3. SUBSTITUTION: "自己換 (Substitution)" with exactly 3 practice lines.
    4. WORD BANK TABLE: Transform the Word Bank into a TABLE with 3 rows: English, Phonics (Empty), and Chinese (Dictionary Def).

    MANDATORY HTML STRUCTURE (Repeat for each line):
    <div class="teaching-box">
        <div class="lyric-header">🎵 (Insert Lyric Line)</div>
        <div class="table-container">
            <table class="word-table">
                <tr><th>English</th><td class="english">Word1</td>...</tr>
                <tr><th>Phonics</th><td class="phonics"></td>...</tr>
                <tr><th>Chinese</th><td class="chinese">正體中文解釋</td>...</tr>
            </table>
        </div>
        
        <div class="section-label">📝 自己翻 (Translate)</div>
        <div class="underline-space"></div>
        
        <div class="section-label">🔄 自己換 (Substitution)</div>
        <div class="sub-practice">
            <b>Pattern:</b> ... <br><b>Example:</b> ... <br>
            <div class="practice-line">1. <span class="sub-line"></span></div>
            <div class="practice-line">2. <span class="sub-line"></span></div>
            <div class="practice-line">3. <span class="sub-line"></span></div>
        </div>

        <div class="section-label">💡 單字庫 (Word Bank Table)</div>
        <div class="table-container">
            <table class="word-table">
                <tr><th>English</th><td class="english">BankWord1</td>...</tr>
                <tr><th>Phonics</th><td class="phonics"></td>...</tr>
                <tr><th>Chinese</th><td class="chinese">正體中文解釋</td>...</tr>
            </table>
        </div>

        <div class="xp-footer">
            <div class="stars">☆☆☆☆☆</div>
            <div class="xp-points">+100 XP</div>
        </div>
    </div>

    OUTPUT HTML ONLY. NO OTHER TEXT.
    """
    return call_gemini_retry(prompt)

def run_v67_engine(title, artist, full_lyrics):
    intro_html = generate_intro_part(title, artist, full_lyrics)
    if not intro_html:
        print("❌ 開頭生成失敗。")
        return None
    
    print("   ☕️ 步驟 A 完成，休息 5 秒...")
    countdown(5)

    # === V62 新邏輯 (Intra-Stanza Dedup + No Skip) ===
    # 1. 切分段落
    stanzas = split_text_into_stanzas(full_lyrics)
    print_status(f"📜 歌詞已切分為 {len(stanzas)} 個段落，準備進行 V62 生成...")
    
    seen_unique_lines = set() # 用來記錄所有已經出現過的句子 (正規化後)
    teaching_html = ""
    
    total_stanzas = len(stanzas)
    processed_count = 0
    
    for i, stanza in enumerate(stanzas):
        # 1. 先清洗段落內容 (過濾短句與噪音)
        clean_stanza = clean_stanza_content(stanza)
        candidate_lines = [l for l in clean_stanza.split('\n') if l.strip()]
        
        if not candidate_lines: 
            continue

        cleaned_original_count = len(candidate_lines)
        unique_lines_in_stanza = []
        
        # V62: 用來檢查「本段落內」已經接受的句子
        local_seen_norms = set()

        # 2. 逐行檢查 (Global + Local Dedup)
        for line in candidate_lines:
            norm_line = clean_line_for_comparison(line)
            if len(norm_line) < 5: 
                continue 
            
            # (A) 檢查是否與「全域已出現」重複 (Global Dedup)
            if is_deep_duplicate(norm_line, seen_unique_lines):
                continue
                
            # (B) V62 新增：檢查是否與「本段落已接受」重複 (Local Intra-Stanza Dedup)
            #     這能抓到 "But the very next day, you gave it away" vs "(You gave it away)"
            if is_deep_duplicate(norm_line, local_seen_norms):
                print(f"   ✂️ [V62] 跳過段落內重複: {line[:30]}...")
                continue

            unique_lines_in_stanza.append((line, norm_line))
            local_seen_norms.add(norm_line) # 加入本地已知

        # 3. V62 修改：取消「重複率 > 50% 整段刪除」的邏輯
        #    改為只檢查是否還有獨特內容保留 (Orphan Filter)
        
        # Orphan Filter: 如果去重後只剩不到 2 行，且原本段落其實很長 (>2)，可能是雜訊
        if len(unique_lines_in_stanza) < 2 and cleaned_original_count > 2:
             print(f"   ✂️ [V62] 跳過孤兒句 (原本 {cleaned_original_count} 行 -> 剩 {len(unique_lines_in_stanza)} 行)")
             # 標記為已看過，避免變體再次出現
             for _, norm in unique_lines_in_stanza:
                seen_unique_lines.add(norm)
             continue

        # === 決定保留，正式轉為輸出 ===
        final_lines_text = []
        for line, norm in unique_lines_in_stanza:
            final_lines_text.append(line)
            seen_unique_lines.add(norm) # 加入全域已知
            
        final_stanza_text = "\n".join(final_lines_text)
        
        if not final_stanza_text: continue

        processed_count += 1
        print_status(f"🔨 [V62] 正在製作段落 {i+1}/{total_stanzas} (去重後剩 {len(final_lines_text)} 行)...")
        
        # 使用清洗+去重後的段落生成
        batch_res = generate_teaching_batch(final_stanza_text)
        
        if batch_res and "<div" in batch_res:
             teaching_html += batch_res + "\n"
        
        if i < total_stanzas - 1:
            wait_time = 5 
            print(f"   ☕️ 段落完成，休息 {wait_time} 秒...")
            countdown(wait_time)
            
    return f"{intro_html}\n{teaching_html}"

if __name__ == "__main__":
    print("\n" + "="*50 + "\n 🌐  Gray 的英文歌詞教材生成器 (V67 Traditional Mode)\n" + "="*50 + "\n")
    setup_model()
    s_name = input("🎤 1. 請輸入歌名: ").strip()
    if not s_name: sys.exit(0)
    s_artist = input("🎤 2. 請輸入歌手: ").strip()

    lyrics, title, artist = search_genius(s_name, s_artist)
    if not lyrics:
        lyrics, title, artist = search_azlyrics(s_name, s_artist)
    if not lyrics:
        try:
            resp = client.models.generate_content(model=CURRENT_MODEL, contents=f"Return full lyrics for '{s_name}' by '{s_artist}'. Text only.")
            lyrics = clean_lyrics_text(resp.text)
            title = s_name; artist = s_artist if s_artist else "Unknown"
        except: pass

    if not lyrics: sys.exit(1)

    body = run_v67_engine(title, artist, lyrics)
    
    if body:
        safe_name = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
        f_path = os.path.join(script_dir, f"{safe_name}_Worksheet_V67.html")
        with open(f_path, "w", encoding="utf-8") as f: f.write(HTML_HEADER + body + HTML_FOOTER)
        print(f"\n🎉 成功！繁體修復 + 單字庫表格化 (V67)。檔案：{f_path}")
        if platform.system() == "Darwin": os.system(f"open '{f_path}'")