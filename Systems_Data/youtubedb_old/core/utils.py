import os
import re
import json
import time
import sys
from typing import Optional, Union, List, Dict, Any
import openai
from google import genai
import chromadb
from chromadb.utils import embedding_functions
from config import OPENAI_API_KEY, GOOGLE_API_KEY, DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

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

# --- AI & Transcription ---

def transcribe_large_audio(audio_path: str, language: str = "zh") -> Optional[str]:
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


def get_or_transcribe(audio_path: str, language: str = "zh") -> Optional[str]:
    """優先讀取已快取的 .txt 逐字稿，省 API 費用"""
    if _HAS_GLOBAL_SKILLS:
        return _get_or_transcribe(audio_path, language=language)
    txt = audio_path.rsplit(".", 1)[0] + ".txt"
    if os.path.exists(txt):
        with open(txt, "r", encoding="utf-8") as f:
            return f.read()
    return transcribe_large_audio(audio_path, language)


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

def load_prompts() -> List[Dict[str, Any]]:
    """載入 prompts.json 中所有 prompt 版本"""
    prompts_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    try:
        with open(prompts_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def get_default_prompt() -> Optional[dict]:
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

def generate_sor_content(title, transcript, model_name="gpt-4o", custom_prompt: Optional[str] = None):
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
    
    try:
        if "gpt-4o" in model_name.lower():
            if not openai_client: return "OpenAI API Key not configured."
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional educational content strategist specializing in the Science of Reading (SoR)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            # Gemini using new SDK
            if not genai_client: return "Google API Key not configured."
            # Use gemini-3-flash-preview as requested by the user
            response = genai_client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=prompt,
                config={'temperature': 0.7}
            )
            return response.text
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg or "429" in error_msg:
            return f"❌ 【OpenAI 額度不足】: 您的 OpenAI 帳戶餘額可能已耗盡或達到限制。建議：\n1. 前往 https://platform.openai.com/usage 檢查帳戶。\n2. 暫時改用 Gemini 模型 (指令增加 --model gemini)。"
        return f"Error generating content: {e}"


def generate_sor_stream(title: str, transcript: str,
                        model_name: str = "gpt-4o",
                        custom_prompt: Optional[str] = None):
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
            yield "❌ OpenAI API Key 未設定"
            return
        stream = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional SoR educational content strategist."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    else:
        # Gemini：一次生成後逐字 yield
        if not genai_client:
            yield "❌ Google API Key 未設定"
            return
        try:
            response = genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"temperature": 0.7}
            )
            text = response.text
            # 每 8 個字 yield 一次，模擬串流感
            for i in range(0, len(text), 8):
                yield text[i:i+8]
        except Exception as e:
            yield f"❌ Gemini 錯誤：{e}"

def get_chroma_collection():
    """Get or create ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    ef = get_embedding_function()
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME, embedding_function=ef)
