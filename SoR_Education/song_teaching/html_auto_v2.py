"""
=============================================================================
🎵 SoR 英文歌詞教材生成器 V2 (Print-First Edition)
=============================================================================
特色：
- SoR 專利音標空白框 (手填)
- 翻譯底線、置換練習、Word Bank 提示字
- 副歌智慧去重 (Hash-based)
- A4 列印優化，完全黑白列印友善
=============================================================================
"""

import os, sys, re, time, hashlib, platform, random, requests
from difflib import SequenceMatcher
from bs4 import BeautifulSoup

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ 請安裝 google-genai: pip install google-genai")
    sys.exit(1)

# ── API ──────────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ 請設定環境變數: export GEMINI_API_KEY='your_key'")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-1.5-flash"

# ── 工具 ─────────────────────────────────────────────────────────────────────
def log(msg): print(f"  {msg}"); sys.stdout.flush()

def countdown(sec):
    for i in range(sec, 0, -1):
        sys.stdout.write(f"\r  ⏳ 等待 {i}s..."); sys.stdout.flush(); time.sleep(1)
    sys.stdout.write("\r  ✅ 繼續！              \n"); sys.stdout.flush()

def call_gemini(prompt, max_tokens=4096):
    for attempt in range(4):
        try:
            r = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.15, max_output_tokens=max_tokens
                )
            )
            return r.text.strip()
        except Exception as e:
            if "429" in str(e) or "exhausted" in str(e):
                wait = 60 + attempt * 30
                log(f"🛑 API 限流，等待 {wait}s ({attempt+1}/4)")
                countdown(wait)
            else:
                log(f"❌ API 錯誤: {e}")
                time.sleep(5)
    return ""

# ── 爬蟲 ─────────────────────────────────────────────────────────────────────
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/121.0.0.0 Safari/537.36'}

def search_genius(song, artist=""):
    log(f"🔍 搜尋 Genius: {song} {artist}")
    try:
        r = requests.get("https://genius.com/api/search/multi",
                         params={'per_page': 5, 'q': f"{song} {artist}"},
                         headers=HEADERS, timeout=10).json()
        hits = r['response']['sections'][0]['hits']
        for h in hits:
            if 'result' not in h: continue
            res = h['result']
            aname = res.get('primary_artist', {}).get('name', '')
            if artist and artist.lower() not in aname.lower(): continue
            log(f"  ✅ 找到: {res['title']} by {aname}")
            lyrics = _download_genius(res['path'])
            return lyrics, res['full_title'], aname
    except Exception as e:
        log(f"  ⚠ Genius 失敗: {e}")
    return None, None, None

def _download_genius(path):
    try:
        page = requests.get(f"https://genius.com{path}", headers=HEADERS, timeout=12)
        soup = BeautifulSoup(page.content, 'html.parser')
        divs = soup.find_all('div', attrs={'data-lyrics-container': 'true'})
        return "\n".join(d.get_text(separator="\n") for d in divs) if divs else None
    except:
        return None

def fallback_gemini_lyrics(song, artist):
    log("🤖 使用 Gemini 補充歌詞...")
    raw = call_gemini(f"Return the full official lyrics for '{song}' by '{artist}'. Include [Verse], [Chorus], [Bridge] section labels. Plain text only, no explanations.")
    return raw if raw and len(raw) > 100 else None

# ── 歌詞解析器 ────────────────────────────────────────────────────────────────
SECTION_RE = re.compile(r'^\[(.+?)\]$')

def parse_lyrics(raw_lyrics):
    """
    將歌詞解析成段落清單：
    [{'type': 'Chorus', 'label': '[Chorus]', 'lines': [...], 'hash': '...'}]
    """
    # 清理
    lines = []
    for line in raw_lyrics.split('\n'):
        line = line.strip()
        if not line: continue
        # 過濾純雜訊行
        if re.fullmatch(r'(oh+|ah+|ooh+|yeah+|la+|na+|mm+|uh+)[\s\-]*', line, re.IGNORECASE):
            continue
        lines.append(line)

    sections = []
    current_type = "Verse"
    current_label = "[Verse 1]"
    current_lines = []

    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            # 保存上一段
            if current_lines:
                sections.append(_make_section(current_type, current_label, current_lines))
                current_lines = []
            current_label = line
            raw_type = m.group(1).strip()
            # 正規化 type
            if "chorus" in raw_type.lower(): current_type = "Chorus"
            elif "bridge" in raw_type.lower(): current_type = "Bridge"
            elif "outro" in raw_type.lower(): current_type = "Outro"
            elif "intro" in raw_type.lower(): current_type = "Intro"
            else: current_type = "Verse"
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(_make_section(current_type, current_label, current_lines))

    return sections

def _make_section(sec_type, label, lines):
    # 過濾短行（少於 3 個詞）
    clean = [l for l in lines if len(l.split()) >= 3]
    text = "\n".join(clean)
    h = hashlib.md5(re.sub(r'\s+', ' ', text.lower()).encode()).hexdigest()[:10]
    return {'type': sec_type, 'label': label, 'lines': clean, 'hash': h}

def deduplicate_sections(sections):
    """
    去重：同 hash 的段落只保留第一次（記錄 is_repeat=True）
    """
    seen_hashes = {}
    result = []
    for sec in sections:
        h = sec['hash']
        if h in seen_hashes:
            repeat_ref = seen_hashes[h]
            result.append({**sec, 'is_repeat': True, 'first_label': repeat_ref['label']})
        else:
            seen_hashes[h] = sec
            result.append({**sec, 'is_repeat': False})
    return result

# ── Gemini 教材生成 ───────────────────────────────────────────────────────────
def generate_section_content(sec, song_title, artist):
    """
    一次 API 呼叫取得：
    - 2-3 個最值得教的句子 (keylines)
    - 每個句子的 3-5 個教學關鍵字 (keywords)
    - 置換句型 (pattern)
    - Word Bank (4-6 個可替換的字，不含原句中的字)

    回傳格式為 JSON-like 結構（用特殊分隔符號，避免 markdown code block 問題）
    """
    lines_text = "\n".join(f"- {l}" for l in sec['lines'][:12])  # 最多12行供選擇

    prompt = f"""You are an English teacher creating a student worksheet for the song "{song_title}" by {artist}.

Section: {sec['label']}
Lyrics:
{lines_text}

Task: Pick the 2-3 BEST lines to teach (most educational vocabulary, not too long, clear meaning).
For each chosen line, provide:
1. The exact line (KEYLINE)
2. 3-5 key vocabulary words from that line worth teaching (KEYWORDS, comma-separated)
3. A substitution pattern using ______ to replace one meaningful word (PATTERN)
4. 4-6 Word Bank words that can fill the blank (WORDBANK, comma-separated, different from original)

RULES:
- Choose lines with real vocabulary (not pure filler words like "oh yeah")
- WORDBANK should be thematic alternatives, not definitions
- Output ONLY in this exact format, repeat for each chosen line:

---LINE---
KEYLINE: [exact lyric line]
KEYWORDS: [word1, word2, word3]
PATTERN: [sentence with ______ replacing one key word]
WORDBANK: [word1, word2, word3, word4]
---END---
"""

    raw = call_gemini(prompt, max_tokens=1500)
    return parse_section_response(raw)

def parse_section_response(raw):
    """解析 Gemini 回傳的結構化文字"""
    blocks = re.findall(r'---LINE---(.*?)---END---', raw, re.DOTALL)
    result = []
    for block in blocks:
        item = {}
        for field in ['KEYLINE', 'KEYWORDS', 'PATTERN', 'WORDBANK']:
            m = re.search(rf'{field}:\s*(.+)', block)
            if m:
                val = m.group(1).strip().strip('"').strip("'")
                if field in ('KEYWORDS', 'WORDBANK'):
                    val = [w.strip() for w in val.split(',') if w.strip()]
                item[field] = val
        if 'KEYLINE' in item and 'KEYWORDS' in item:
            result.append(item)
    return result

def generate_cover_story(song_title, artist):
    log("📖 生成歌曲背景故事...")
    prompt = f"""用繁體中文（台灣）寫一段 80-120 字的歌曲介紹，給台灣國中/高中英文課學生看。
歌曲：《{song_title}》by {artist}
包含：這首歌的文化背景、有趣故事或歷史意義。
只輸出文字內容，不要標題，不要 markdown。"""
    return call_gemini(prompt, max_tokens=400)

# ── HTML 生成 ─────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Outfit:wght@400;700;900&display=swap');

/* ── 列印設定 ── */
@page { size: A4 portrait; margin: 1.4cm 1.8cm; }

* { box-sizing: border-box; }

body {
    font-family: 'Outfit', 'Noto Sans TC', sans-serif;
    background: #fff;
    color: #1a1a1a;
    margin: 0;
    padding: 20px;
    font-size: 14px;
    line-height: 1.6;
}

/* ── 封面 ── */
.cover {
    text-align: center;
    padding: 40px 20px;
    border: 3px solid #1a1a1a;
    border-radius: 12px;
    margin-bottom: 30px;
    page-break-after: always;
}
.cover h1 { font-size: 2.4em; font-weight: 900; margin: 0 0 6px 0; }
.cover .artist { font-size: 1.2em; color: #444; margin-bottom: 20px; }
.cover .qr-wrap { display: inline-block; border: 2px solid #1a1a1a; padding: 10px; border-radius: 8px; margin: 16px; }
.cover .qr-wrap p { font-size: 0.75em; margin: 6px 0 0 0; color: #555; }
.cover .story { text-align: left; background: #f8f8f8; border-left: 5px solid #1a1a1a; padding: 14px 18px; font-size: 0.95em; color: #333; border-radius: 0 6px 6px 0; margin-top: 20px; }

/* ── 歌詞總覽 ── */
.lyrics-overview {
    border: 2px dashed #aaa;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 30px;
    page-break-after: always;
}
.lyrics-overview h2 { font-size: 1.1em; font-weight: 900; margin: 0 0 12px 0; }
.lyrics-overview .section-label { font-weight: 700; color: #555; font-size: 0.82em; text-transform: uppercase; margin: 12px 0 4px 0; }
.lyrics-overview p { margin: 2px 0; font-size: 0.92em; color: #333; }

/* ── 教學框 ── */
.section-box {
    border: 2px solid #1a1a1a;
    border-radius: 10px;
    margin-bottom: 28px;
    page-break-inside: avoid;
    overflow: hidden;
}
.section-header {
    background: #1a1a1a;
    color: white;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 0.88em;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.section-header .stars { color: #f1c40f; font-size: 1.1em; letter-spacing: 3px; cursor: pointer; }

/* 歌詞行 */
.lyric-line {
    font-size: 1.5em;
    font-weight: 900;
    padding: 12px 16px 6px 16px;
    border-bottom: 1px solid #ddd;
    color: #1a1a1a;
    font-family: 'Outfit', sans-serif;
}

/* 音標區 */
.phonics-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    padding: 12px 16px 6px 16px;
    border-bottom: 1px solid #ddd;
    align-items: flex-end;
}
.phonics-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
.phonics-item .kw-label {
    font-weight: 700;
    font-size: 1.05em;
    color: #1a1a1a;
}
.phonics-box {
    width: 90px;
    height: 46px;
    border: 1.5px solid #333;
    border-radius: 5px;
    background: white;
    /* 空白供手寫 */
}
.phonics-section-label {
    font-size: 0.75em;
    font-weight: 700;
    color: #888;
    text-transform: uppercase;
    padding: 6px 16px 2px 16px;
    letter-spacing: 1px;
}

/* 翻譯區 */
.translate-row {
    padding: 10px 16px;
    border-bottom: 1px solid #ddd;
    display: flex;
    align-items: baseline;
    gap: 10px;
}
.translate-row .t-label {
    font-weight: 700;
    font-size: 0.82em;
    white-space: nowrap;
}
.write-line {
    flex: 1;
    border-bottom: 1.5px solid #333;
    min-height: 28px;
}

/* 置換區 */
.sub-row {
    padding: 10px 16px;
    border-bottom: 1px solid #ddd;
}
.sub-row .sub-label {
    font-weight: 700;
    font-size: 0.82em;
    margin-bottom: 4px;
}
.pattern-line {
    font-size: 0.95em;
    color: #444;
    margin-bottom: 8px;
    font-style: italic;
}

/* Word Bank */
.wordbank-row {
    padding: 8px 16px;
    border-bottom: 1px solid #ddd;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}
.wb-label {
    font-size: 0.8em;
    font-weight: 700;
    color: #666;
    margin-right: 4px;
}
.wb-chip {
    border: 1px solid #333;
    padding: 2px 10px;
    border-radius: 3px;
    font-size: 0.88em;
    font-weight: 600;
}

/* 練習底線 */
.practice-lines {
    padding: 8px 16px 14px 16px;
}
.pline {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 8px;
}
.pline .num {
    font-size: 0.85em;
    font-weight: 700;
    min-width: 16px;
}
.pline .pwrite-line {
    flex: 1;
    border-bottom: 1px solid #999;
    min-height: 26px;
}

/* 副歌回顧卡 */
.repeat-card {
    border: 2px dashed #999;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    color: #666;
    margin-bottom: 24px;
    page-break-inside: avoid;
}
.repeat-card .rc-icon { font-size: 2em; }
.repeat-card p { margin: 6px 0 0 0; font-size: 0.9em; }

/* 螢幕預覽專用樣式 */
@media screen {
    body { background: #f0ede8; padding: 30px; }
    .section-box { max-width: 820px; margin: 0 auto 32px auto; box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
    .cover { max-width: 820px; margin: 0 auto 30px auto; box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
    .lyrics-overview { max-width: 820px; margin: 0 auto 30px auto; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
    .lyric-line { color: #c0392b; }
}

/* 列印隱藏 */
@media print {
    body { padding: 0; background: white; }
    .section-box { box-shadow: none; }
    .stars { display: none; } /* 列印不需要星星 */
}
</style>
"""

def build_cover(title, artist, story, qr_url):
    story_html = story.replace('\n', '<br>') if story else "這是一首膾炙人口的英文歌曲。"
    return f"""
<div class="cover">
    <h1>🎵 {title}</h1>
    <div class="artist">by {artist}</div>
    <div class="qr-wrap">
        <img src="{qr_url}" width="120" height="120" alt="QR Code">
        <p>📱 Scan to listen</p>
    </div>
    <div class="story">{story_html}</div>
</div>"""

def build_lyrics_overview(sections):
    rows = []
    for sec in sections:
        rows.append(f'<div class="section-label">{sec["label"]}</div>')
        for line in sec['lines']:
            rows.append(f'<p>{line}</p>')
    return f"""
<div class="lyrics-overview">
    <h2>📄 完整歌詞 Complete Lyrics</h2>
    {"".join(rows)}
</div>"""

def build_repeat_card(sec):
    return f"""
<div class="repeat-card">
    <div class="rc-icon">🔁</div>
    <strong>{sec["label"]}</strong>
    <p>副歌回來了！請翻回前面複習 (Chorus — see above)</p>
</div>"""

def build_section_box(sec_label, line_data_list, sec_index):
    """
    sec_label: e.g. "[Chorus]"
    line_data_list: list of dicts from parse_section_response
    """
    lines_html = []
    for idx, item in enumerate(line_data_list):
        keyline = item.get('KEYLINE', '')
        keywords = item.get('KEYWORDS', [])[:5]
        pattern = item.get('PATTERN', '')
        wordbank = item.get('WORDBANK', [])[:6]

        # 音標框
        phonics_items = "".join(
            f'<div class="phonics-item"><div class="kw-label">{kw}</div><div class="phonics-box"></div></div>'
            for kw in keywords
        )

        # 置換練習底線數量：句子短（<7字）給3條，否則給2條
        word_count = len(keyline.split())
        line_count = 3 if word_count < 7 else 2
        practice = "".join(
            f'<div class="pline"><span class="num">{i+1}.</span><div class="pwrite-line"></div></div>'
            for i in range(line_count)
        )

        # Word Bank chips
        chips = "".join(f'<span class="wb-chip">{w}</span>' for w in wordbank)

        lines_html.append(f"""
        <div class="lyric-line">🎵 {keyline}</div>

        <div class="phonics-section-label">SoR 專利音標 (填寫音標)</div>
        <div class="phonics-row">{phonics_items}</div>

        <div class="translate-row">
            <span class="t-label">📝 我的翻譯：</span>
            <div class="write-line"></div>
        </div>

        <div class="sub-row">
            <div class="sub-label">🔄 置換練習 Substitution</div>
            <div class="pattern-line">Pattern: {pattern}</div>
        </div>

        <div class="wordbank-row">
            <span class="wb-label">💡 Word Bank：</span>
            {chips}
        </div>

        <div class="practice-lines">{practice}</div>
        {"<hr style='border:none;border-top:2px dashed #ddd;margin:4px 0'>" if idx < len(line_data_list)-1 else ""}
        """)

    star_id = f"stars-{sec_index}"
    return f"""
<div class="section-box">
    <div class="section-header">
        <span>{sec_label}</span>
        <span class="stars" id="{star_id}" onclick="rateStar(this)">☆☆☆☆☆</span>
    </div>
    {"".join(lines_html)}
</div>"""

HTML_SCRIPT = """
<script>
function rateStar(el) {
    const seq = ['☆☆☆☆☆','★☆☆☆☆','★★☆☆☆','★★★☆☆','★★★★☆','★★★★★'];
    const cur = el.innerText;
    const i = seq.indexOf(cur);
    el.innerText = seq[(i+1) % seq.length];
}
</script>
"""

def build_html(title, artist, cover_html, overview_html, body_sections_html):
    qr_label_title = title.replace(' ', '+')
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎵 {title} by {artist} — SoR Worksheet</title>
{CSS}
</head>
<body>
{cover_html}
{overview_html}
{"".join(body_sections_html)}
{HTML_SCRIPT}
</body>
</html>"""

# ── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  🎵 SoR 英文歌詞教材生成器 V2 (Print-First Edition)")
    print("="*55 + "\n")

    song = input("🎤 歌名：").strip()
    if not song: sys.exit(0)
    artist = input("🎤 歌手：").strip()

    # 1. 爬歌詞
    lyrics, full_title, full_artist = search_genius(song, artist)
    if not lyrics:
        lyrics = fallback_gemini_lyrics(song, artist)
        full_title = song; full_artist = artist or "Unknown"

    if not lyrics or len(lyrics) < 80:
        print("❌ 找不到歌詞，請換一首試試。"); sys.exit(1)

    log(f"✅ 歌詞取得完成 ({len(lyrics)} 字元)")
    countdown(3)

    # 2. 解析 + 去重
    sections = parse_lyrics(lyrics)
    sections = deduplicate_sections(sections)
    unique_count = sum(1 for s in sections if not s.get('is_repeat'))
    log(f"📋 段落解析：{len(sections)} 段，去重後唯一段落 {unique_count} 個")

    # 3. 封面故事
    story = generate_cover_story(full_title, full_artist)
    countdown(5)

    # 4. 歌詞總覽
    unique_sections = [s for s in sections if not s.get('is_repeat')]
    overview_html = build_lyrics_overview(unique_sections)

    # 5. 封面
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://www.youtube.com/results?search_query={full_title.replace(' ','+')}+{full_artist.replace(' ','+')}+lyrics"
    cover_html = build_cover(full_title, full_artist, story, qr_url)

    # 6. 逐段生成
    body_parts = []
    total = len(sections)
    for i, sec in enumerate(sections):
        log(f"🔨 [{i+1}/{total}] 處理段落: {sec['label']} {'(重複→跳過)' if sec.get('is_repeat') else ''}")

        if sec.get('is_repeat'):
            body_parts.append(build_repeat_card(sec))
            continue

        if not sec['lines']:
            continue

        # 生成教材
        line_data = generate_section_content(sec, full_title, full_artist)
        if not line_data:
            log(f"  ⚠ {sec['label']} 生成失敗，跳過")
            continue

        body_parts.append(build_section_box(sec['label'], line_data, i))

        if i < total - 1:
            countdown(5)

    # 7. 輸出
    safe = re.sub(r'[^\w\s-]', '', full_title).strip().replace(' ', '_')
    out_path = os.path.join(SCRIPT_DIR, f"{safe}_SoR_Worksheet.html")
    html = build_html(full_title, full_artist, cover_html, overview_html, body_parts)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n{'='*55}")
    print(f"  🎉 完成！")
    print(f"  📄 {out_path}")
    print(f"{'='*55}\n")
    if platform.system() == "Darwin":
        os.system(f"open '{out_path}'")

if __name__ == "__main__":
    main()
