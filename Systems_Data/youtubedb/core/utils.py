import os
import re
import json
import time
import sys
import openai
from google import genai
import chromadb
from chromadb.utils import embedding_functions
from config import OPENAI_API_KEY, GOOGLE_API_KEY, OPENROUTER_API_KEY, DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

# ── Global_Skills 整合 ────────────────────────────────────────────────────────
# 讓 Global_Skills 可被 import（youtubedb 在 python project/ 子資料夾下）
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from Global_Skills.audio_transcriber.audio_transcriber import (
        transcribe_audio as _transcribe_large,
        get_or_transcribe as _get_or_transcribe,
    )
    _HAS_GLOBAL_SKILLS = True
except ImportError:
    _HAS_GLOBAL_SKILLS = False

# Configure APIs
if OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None

if GOOGLE_API_KEY:
    genai_client = genai.Client(api_key=GOOGLE_API_KEY)
else:
    genai_client = None

if OPENROUTER_API_KEY:
    openrouter_client = openai.OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8501", 
            "X-Title": "SoR Video System",
        }
    )
else:
    openrouter_client = None

# --- AI & Transcription ---

def transcribe_large_audio(audio_path: str, language: str = "zh") -> str | None:
    """
    轉錄音訊，自動處理超過 24MB 的大檔案（切割後逐段聽寫）。
    若 Global_Skills 已安裝，使用 audio_transcriber skill；
    否則 fallback 到簡易版（小檔直接轉，大檔報錯）。
    """
    if _HAS_GLOBAL_SKILLS:
        return _transcribe_large(audio_path, language=language)

    # Fallback：無 Global_Skills 時的簡易版
    if not openai_client:
        print("❌ OpenAI API Key 未設定")
        return None
    try:
        with open(audio_path, "rb") as f:
            resp = openai_client.audio.transcriptions.create(
                model="whisper-1", file=f, language=language
            )
        return resp.text
    except Exception as e:
        print(f"❌ 聽寫失敗：{e}")
        return None


def get_or_transcribe(audio_path: str, language: str = "zh") -> str | None:
    """優先讀取已快取的 .txt 逐字稿，省 API 費用"""
    if _HAS_GLOBAL_SKILLS:
        return _get_or_transcribe(audio_path, language=language)
    txt = audio_path.rsplit(".", 1)[0] + ".txt"
    if os.path.exists(txt):
        with open(txt, "r", encoding="utf-8") as f:
            return f.read()
    return transcribe_large_audio(audio_path, language)


def shift_srt_time(srt_content, offset_seconds):
    """將 SRT 內容中的所有時間戳偏移指定的秒數"""
    if offset_seconds == 0:
        return srt_content
    
    import re
    from datetime import timedelta
    
    def shift_match(match):
        time_str = match.group(0)
        try:
            h, m, s = time_str.replace(',', '.').split(':')
            t = timedelta(hours=int(h), minutes=int(m), seconds=float(s))
            new_t = t + timedelta(seconds=offset_seconds)
            total_seconds = new_t.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            return f"{hours:02}:{minutes:02}:{seconds:06.3f}".replace('.', ',')
        except:
            return time_str
    return re.sub(r'\d{2}:\d{2}:\d{2},\d{3}', shift_match, srt_content)

def transcribe_audio_to_srt(audio_path):
    """使用 OpenAI Whisper 將音訊轉譯為 SRT 格式 (具備重試機制)"""
    if not openai_client:
        return "Error: OpenAI API Key not configured."
    
    import time
    for attempt in range(3):
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="srt"
                )
            return transcript
        except Exception as e:
            if attempt < 2:
                print(f"⚠️ 轉譯嘗試 {attempt+1} 失敗，將在 5 秒後重試... ({e})")
                time.sleep(5)
            else:
                return f"Error in transcription after 3 attempts: {e}"

def transcribe_audio_to_srt_large(audio_path, download_dir, source_dir, base_name, msg_callback=None):
    """
    轉譯大檔案，自動處理超過 25MB 的限制，並支援進度回報。
    """
    file_size = os.path.getsize(audio_path)
    max_size = 24.5 * 1024 * 1024 
    
    if file_size <= max_size:
        return transcribe_audio_to_srt(audio_path)
    
    # 大檔案處理：自動分割
    import subprocess
    segment_pattern = os.path.join(download_dir, f"{base_name}_seg_%03d.mp3")
    if msg_callback: msg_callback(f"檔案較大，正在進行音訊分割...", "🔪")
    subprocess.run([
        'ffmpeg', '-i', audio_path, 
        '-f', 'segment', '-segment_time', '1200', 
        '-c', 'copy', '-y', segment_pattern
    ], check=True, capture_output=True)
    
    segments = sorted([f for f in os.listdir(download_dir) if re.match(re.escape(base_name) + r"_seg_\d+\.mp3", f)])
    total_segs = len(segments)
    if msg_callback: msg_callback(f"已切割為 {total_segs} 個區段，開始依序轉錄...", "📋")
    
    full_srt = ""
    for i, seg in enumerate(segments):
        seg_path = os.path.join(download_dir, seg)
        if msg_callback: msg_callback(f"正在轉錄第 {i+1}/{total_segs} 段...", "🎙️")
        
        # 解析偏移時間
        match = re.search(r'seg_(\d+)', seg)
        offset = int(match.group(1)) * 1200 if match else 0
        
        seg_srt = transcribe_audio_to_srt(seg_path)
        if not seg_srt or "Error" in seg_srt:
            full_srt += f"\n\n[TRANSCRIPTION ERROR IN SECTION {i+1}]\n\n"
        else:
            shifted_srt = shift_srt_time(seg_srt, offset)
            full_srt += shifted_srt + "\n\n"
        
        try: os.remove(seg_path)
        except: pass
        
    return full_srt

# --- Utility Functions ---

def clean_srt_to_text(srt_content):
    """Remove timestamps and sequence numbers from SRT content, returning pure text."""
    lines = srt_content.splitlines()
    cleaned_lines = []
    
    timecode_pattern = re.compile(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$')
    seq_pattern = re.compile(r'^\d+$')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        if timecode_pattern.match(line): continue
        if seq_pattern.match(line): continue
        cleaned_lines.append(line)
        
    return " ".join(cleaned_lines)

def parse_srt_time(time_str):
    """Convert SRT time string to seconds."""
    hours, minutes, seconds = time_str.replace(',', '.').split(':')
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

def parse_srt_file(file_path, target_chunk_size=300):
    """Parse SRT into semantic chunks."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []

    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
    matches = pattern.findall(content)

    chunks = []
    current_chunk_text = ""
    current_start_time = None

    for i, match in enumerate(matches):
        start_str = match[1]
        end_str = match[2]
        text = match[3].replace('\n', ' ').strip()
        
        if current_chunk_text == "":
            current_start_time = parse_srt_time(start_str)
        
        current_chunk_text += text + " "
        
        if len(current_chunk_text) >= target_chunk_size or i == len(matches) - 1:
            end_time = parse_srt_time(end_str)
            chunks.append({
                "text": current_chunk_text.strip(),
                "start": current_start_time,
                "end": end_time
            })
            current_chunk_text = ""
            current_start_time = None
            
    return chunks

def chunk_text_generic(text, target_chunk_size=500):
    """將一般純文字切成知識點片段，用於沒有 SRT 的文字來源"""
    # 依段落切割
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        
        if len(current_chunk) + len(p) < target_chunk_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

# --- AI & Database ---

# ── Prompt 管理 ───────────────────────────────────────────────────────────────

def load_prompts() -> list[dict]:
    """載入 prompts.json 中所有 prompt 版本"""
    prompts_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    try:
        with open(prompts_path, "r", encoding="utf-8") as f:
            content = f.read()
            return json.loads(content)
    except Exception:
        return []

def get_default_prompt() -> dict | None:
    """取得預設 prompt（is_default=True 的那筆）"""
    for p in load_prompts():
        if p.get("is_default"):
            return p
    prompts = load_prompts()
    return prompts[0] if prompts else None

def get_embedding_function():
    """Initialize ChromaDB embedding function — lazy load, only on first call."""
    # 用 module-level cache：第一次才真正載入模型，之後直接回傳快取
    if not hasattr(get_embedding_function, "_cached"):
        get_embedding_function._cached = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
        )
    return get_embedding_function._cached

def generate_sor_content(title, transcript, model_name="gpt-4o", custom_prompt: str | None = None):
    """Generate SoR strategy content using GPT-4o or Gemini.
    
    custom_prompt: 若提供，直接使用此 prompt（需含 {title} 與 {transcript} 佔位符）
                   若為 None，從 prompts.json 載入預設版本
    """
    # ── 決定使用哪個 prompt ──────────────────────────────────────────────────
    if custom_prompt:
        prompt = custom_prompt.format(title=title, transcript=transcript)
    else:
        default = get_default_prompt()
        if default and "{title}" in default.get("template", ""):
            prompt = default["template"].format(title=title, transcript=transcript)
        else:
            # Fallback：硬編碼原始 SOP
            prompt = f"""
    你現在是【蕭博士 SoR 美語】的文案策略總監。
    請嚴格執行【蕭博士 SoR 文案生產 SOP (Ver 2.0)】，為這段影片產出深度分析。

    影片標題：{title}
    逐字稿內容：
    {transcript}

    ---
    ### 核心產出規範（必須達到此厚度與專業感）
    1. 【理論背景（科學靈魂）】：篇幅要長，需引用科學機制（如神經連結、髓鞘化、大腦皮層與肌肉記憶）。不可只寫定義，要解釋運作原理。
    2. 【優化觀念（比喻外殼）】：擴充比喻的畫面感，解釋「為什麼」用這個比喻，讓家長產生強烈頓悟。
    3. 【實戰 Q&A】：10 組回答，遵守「靈魂一樣，外殼不同」原則，文字要親切且具專業說服力。

    ### 任務開始
    請參照上述範例的厚度、專業深度與親切口吻，為本次提供之逐字稿產出完整文案（嚴格禁止條列式縮水）：
    """
    
    import time
    for attempt in range(3):
        try:
            if "gpt-5.4" in model_name.lower():
                target_gpt = "gpt-5.4-2026-03-05"
                gpt_params = {"max_completion_tokens": 16384}
            else:
                target_gpt = "gpt-4o"
                gpt_params = {"max_tokens": 8192}
                
            if "gpt" in model_name.lower():
                if not openai_client: return "OpenAI API Key not configured."
                response = openai_client.chat.completions.create(
                    model=target_gpt,
                    messages=[
                        {"role": "system", "content": "You are a professional SoR educational content strategist. ALWAYS provide the full 10 Q&A pairs requested. DO NOT truncate or summarize due to length."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    **gpt_params
                )
                return response.choices[0].message.content
            elif "claude" in model_name.lower() or "openrouter" in model_name.lower():
                if not openrouter_client: return "OpenRouter API Key not configured."
                # Mapping: If "claude" is in the name, use OpenRouter's Claude 3.5 Sonnet
                target = "anthropic/claude-3.5-sonnet" if "claude" in model_name.lower() else model_name.replace("openrouter/", "")
                response = openrouter_client.chat.completions.create(
                    model=target,
                    messages=[
                        {"role": "system", "content": "You are a professional SoR educational content strategist. ALWAYS provide the full 10 Q&A pairs requested. DO NOT truncate or summarize due to length."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4096
                )
                return response.choices[0].message.content
            elif "gemini" in model_name.lower():
                if not genai_client: return "Google API Key not configured."
                # Determine which Gemini to use
                if "3-flash" in model_name:
                    models_to_try = ["gemini-3-flash-preview", "gemini-3-flash"]
                elif "2.5-flash" in model_name:
                    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
                else:
                    models_to_try = ["gemini-3-flash-preview", "gemini-2.5-flash"]
                
                last_err = None
                for m_name in models_to_try:
                    try:
                        response = genai_client.models.generate_content(
                            model=m_name, 
                            contents=prompt,
                            config={'temperature': 0.7}
                        )
                        return response.text
                    except Exception as e:
                        last_err = str(e)
                        if any(x in last_err.lower() for x in ["404", "not_found", "no longer available", "not found", "410"]):
                            continue 
                        raise e 
                return f"❌ 嘗試所有指定模型均失敗：\n最後一個錯誤: {last_err}"
            else:
                return f"❌ 未知的模型類型: {model_name}"
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < 2:
                wait_time = 5 * (attempt + 1)
                time.sleep(wait_time)
                continue
            
            if "insufficient_quota" in error_msg or "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return f"❌ 【API 額度/頻率限制】: \n- 詳細錯誤: {error_msg}\n- 建議：\n  1. 前往控制台檢查配額。\n  2. 稍等幾分鐘後再試 (RPS 限制)。\n  3. 切換模型（若 Gemini 爆掉可試試 GPT-4o 或反之）。"
            try:
                msg = str(e)
            except UnicodeEncodeError:
                msg = repr(e)
            return f"Error generating content: {msg}"
    return "Error: Multiple attempts failed."


def generate_sor_stream(title: str, transcript: str,
                        model_name: str = "gpt-4o",
                        custom_prompt: str | None = None):
    """Streaming 版文案生成，回傳 generator，供 st.write_stream() 使用。
    僅 GPT-4o 支援真正串流；Gemini 一次回傳後逐字 yield（模擬串流）。
    """
    # 決定 prompt
    if custom_prompt:
        prompt = custom_prompt.format(title=title, transcript=transcript)
    else:
        default = get_default_prompt()
        if default and "{title}" in default.get("template", ""):
            prompt = default["template"].format(title=title, transcript=transcript)
        else:
            prompt = f"請為影片「{title}」的逐字稿生成 SoR 文案：\n{transcript}"

    if "gpt" in model_name.lower():
        if not openai_client:
            raise RuntimeError("❌ OpenAI API Key 未設定")
            
        if "gpt-5.4" in model_name.lower():
            target_gpt = "gpt-5.4-2026-03-05"
            gpt_params = {"max_completion_tokens": 16384}
        else:
            target_gpt = "gpt-4o"
            gpt_params = {"max_tokens": 8192}

        stream = openai_client.chat.completions.create(
            model=target_gpt,
            messages=[
                {"role": "system", "content": "You are a professional SoR educational content strategist. ALWAYS provide the full 10 Q&A pairs requested. DO NOT truncate or summarize due to length."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.7,
            stream=True,
            **gpt_params
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    elif "claude" in model_name.lower() or "openrouter" in model_name.lower():
        if not openrouter_client:
            raise RuntimeError("❌ OpenRouter API Key 未設定")
        target = "anthropic/claude-3.5-sonnet" if "claude" in model_name.lower() else model_name.replace("openrouter/", "")
        stream = openrouter_client.chat.completions.create(
            model=target,
            messages=[
                {"role": "system", "content": "You are a professional SoR educational content strategist. ALWAYS provide the full 10 Q&A pairs requested. DO NOT truncate or summarize due to length."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    elif "gemini" in model_name.lower():
        if not genai_client:
            raise RuntimeError("❌ Google API Key 未設定")
        import time
        # 決定嘗試順序
        if "3-flash" in model_name:
            models_to_try = ["gemini-3-flash-preview", "gemini-3-flash"]
        elif "2.5-flash" in model_name:
            models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
        else:
            models_to_try = ["gemini-3-flash-preview", "gemini-2.5-flash"]

        final_err = None
        for attempt in range(2):
            success = False
            try:
                for m_name in models_to_try:
                    try:
                        response = genai_client.models.generate_content(
                            model=m_name,
                            contents=prompt,
                            config={"temperature": 0.7}
                        )
                        text = response.text
                        for i in range(0, len(text), 8):
                            yield text[i:i+8]
                        success = True
                        break
                    except Exception as e:
                        err_str = str(e).lower()
                        if any(x in err_str for x in ["404", "not_found", "no longer available", "not found", "410"]):
                            continue
                        raise e
                if success: break
                else: final_err = "❌ 嘗試指定的模型連線均失敗，請確認配額。"
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg and attempt < 1:
                    time.sleep(5)
                    continue
                final_err = f"❌ Gemini 錯誤：{err_msg}"
                break # 429 以外的重大錯誤 (如 403) 直接跳出
        
        if not success:
            raise RuntimeError(final_err)

def detect_speech_start(audio_path: str, model_name: str = "gemini-2.5-flash") -> float:
    """使用 Gemini 偵測人聲開始的時間點（秒）。"""
    if not genai_client:
        return 0.0
    
    # 1. 提取前 60 秒的音訊片段作為預覽
    import subprocess
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # 快速提取前 60 秒
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_path, "-t", "60", 
            "-acodec", "libmp3lame", "-q:a", "9", tmp_path
        ], check=True, capture_output=True)
        
        # 2. 上傳並讓 Gemini 分析
        prompt = "Listen to this audio. At exactly how many seconds does the actual human speech or teaching content begin? Return only the number of seconds (e.g., 12.5). If it starts immediately, return 0. Do not provide any other text."
        
        # 用於音訊的特別上傳方式 (如果是 2.5/3.0 版本模型)
        with open(tmp_path, "rb") as f:
            audio_data = f.read()
            
        response = genai_client.models.generate_content(
            model=model_name if "gemini" in model_name else "gemini-2.5-flash",
            contents=[prompt, {"mime_type": "audio/mp3", "data": audio_data}],
            config={'temperature': 0.0}
        )
        
        # 3. 解析結果
        text = response.text.strip()
        # 提取數字
        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception as e:
        print(f"⚠️ AI 偵測人聲失敗: {e}")
        return 0.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def get_chroma_collection():
    """Get or create ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    ef = get_embedding_function()
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME, embedding_function=ef)
