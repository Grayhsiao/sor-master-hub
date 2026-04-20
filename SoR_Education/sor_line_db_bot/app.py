import os
import uuid
import tempfile
import re
import logging
from flask import Flask, request, abort, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, AudioMessage, TextSendMessage, AudioSendMessage, TextMessage
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv
from term_corrector import TermCorrector
from vector_service import VectorService

# ==========================================
# 0. 初始化與日誌設定
# ==========================================
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
OPEN_AI_API_KEY = os.getenv('OPENAI_API_KEY', '') # 保留給預設的 Whisper/TTS 用
BASE_URL = os.getenv('BASE_URL', 'https://xxxx.ngrok-free.app')

# LineOA 模組專屬大腦設定
LINEOA_PROVIDER = os.getenv('LINEOA_PROVIDER', 'OpenAI')
LINEOA_API_KEY = os.getenv('LINEOA_API_KEY', OPEN_AI_API_KEY)
LINEOA_MODEL = os.getenv('LINEOA_MODEL', 'gpt-4o')

# 初始化服務
vector_svc = VectorService()
corrector = TermCorrector()

# ==========================================
# 1. 對話記憶管理 (Session Manager)
# ==========================================
class SessionManager:
    def __init__(self, max_turns=3):
        self.sessions = {}
        self.max_turns = max_turns

    def get_history(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        return self.sessions[user_id]

    def add_message(self, user_id, role, content):
        history = self.get_history(user_id)
        history.append({"role": role, "content": content})
        # 保持在指定的對話輪數內 (1 輪 = 1 user + 1 assistant)
        if len(history) > self.max_turns * 2:
            self.sessions[user_id] = history[-(self.max_turns * 2):]

session_manager = SessionManager(max_turns=3)

# ==========================================
# 2. 蕭博士的人設指令 (數位分身核心)
# ==========================================
SYSTEM_BASE_PROMPT = """
你現在就是【蕭博士】本人。請以此身份提供專業、溫潤且具備教育高度的服務。

【核心原則】
1. **身份與語氣**：請用「我」自稱。我是致力於 SoR (Sound-Oriented Reading) 的語言教育專家。語氣要像一個專業教練同事也充滿長輩的溫厚感。
2. **同理心優先**：當家長提到英文學習瓶頸或焦慮時，請先給予同理心（例如：「我非常懂你的焦慮...」、「辛苦了...」）。
3. **依據回答**：請嚴格參考我提供給你的【參考資料】來回答問題。
4. **遇事不決處理**：如果【參考資料】中完全沒有相關答案，不可自行編造。請溫馨回應：「這題我目前還沒拍過專門影片，我先記在小本子上。你可以先從基礎的聲音積木（PA）開始練習...」。
5. **語音與簡潔性**：回答內容（不含末尾行銷）請控制在 **80 字以內**。口氣要「像在對話」，而不是在朗讀，多用「喔！」、「其實啊...」來增加親切度。
6. **行銷導購**：回答結尾必須引用資料中相關的【對應行銷】文案 (CTA)。
"""

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPEN_AI_API_KEY) 

STATIC_DIR = 'static'
if not os.path.exists(STATIC_DIR): os.makedirs(STATIC_DIR)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

def speech_to_text(audio_path):
    try:
        with open(audio_path, "rb") as f:
            return client.audio.transcriptions.create(model="whisper-1", file=f, language="zh").text
    except Exception as e:
        logger.error(f"Whisper Error: {e}")
        return None

def generate_text_reply(user_id, user_input):
    try:
        # 輸入端術語修正
        user_input = corrector.correct(user_input)
        
        # 動態檢索最相關的知識
        relevant_knowledge, sources = vector_svc.query(user_input)
        
        # 獲取歷史紀錄
        history = session_manager.get_history(user_id)
        
        # 組合 Messages
        system_content = f"{SYSTEM_BASE_PROMPT}\n\n【參考資料】\n{relevant_knowledge}"
        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        
        base_reply = "API Provider 設定錯誤"
        
        # 依據 Hub 選擇的大腦供應商呼叫 API
        if "Gemini" in LINEOA_PROVIDER:
            import google.generativeai as genai
            genai.configure(api_key=LINEOA_API_KEY)
            
            # 將 openAI 格式轉換為 gemini 格式
            gemini_msgs = []
            for m in history:
                role = "user" if m["role"] == "user" else "model"
                gemini_msgs.append({"role": role, "parts": [m["content"]]})
            gemini_msgs.append({"role": "user", "parts": [user_input]})
            
            model_name = LINEOA_MODEL if LINEOA_MODEL else "gemini-1.5-flash"
            model = genai.GenerativeModel(model_name, system_instruction=system_content)
            response = model.generate_content(gemini_msgs)
            base_reply = response.text
             
        else:
            # OpenAI / OpenRouter / DeepSeek 共用 OpenAI SDK
            kws = {"api_key": LINEOA_API_KEY}
            if "OpenRouter" in LINEOA_PROVIDER:
                kws["base_url"] = "https://openrouter.ai/api/v1"
            elif "DeepSeek" in LINEOA_PROVIDER:
                kws["base_url"] = "https://api.deepseek.com"
                
            temp_client = OpenAI(**kws)
            model_name = LINEOA_MODEL if LINEOA_MODEL else "gpt-4o"
            
            completion = temp_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.3
            )
            base_reply = completion.choices[0].message.content
        
        # 附加來源標註
        if sources:
            source_labels = "、".join([f"#{s}" for s in sources])
            source_footer = f"\n\n📚 資料來源：蕭博士教學編號 {source_labels}"
            if "資料來源" not in base_reply:
                base_reply += source_footer
        
        # 輸出端術語修正
        base_reply = corrector.correct(base_reply)
        
        # 存入記憶
        session_manager.add_message(user_id, "user", user_input)
        session_manager.add_message(user_id, "assistant", base_reply)
                
        return base_reply
    except Exception as e:
        logger.error(f"GPT Error: {e}")
        return "抱歉，蕭博士的大腦開了點小差，請再試一次。"

def generate_voice_openai(text):
    try:
        # 語音前置處理：移除來源標註與導購，只唸核心回覆
        speech_text = text.split("📚 資料來源")[0].split("👉")[0]
        speech_text = speech_text.replace("SoR", "S.O.R.")
        
        response = client.audio.speech.create(model="tts-1", voice="onyx", input=speech_text)
        filename = f"reply_{uuid.uuid4()}.mp3"
        filepath = os.path.join(STATIC_DIR, filename)
        response.stream_to_file(filepath)
        return filepath, f"{BASE_URL}/static/{filename}"
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None, None

def process_and_reply(event, user_text=None, audio_file_path=None):
    user_id = event.source.user_id
    
    # 傳送「收到」提示
    try: line_bot_api.push_message(user_id, TextSendMessage(text="👂 蕭博士思考中..."))
    except: pass

    try:
        final_input = user_text
        if audio_file_path:
            transcribed = speech_to_text(audio_file_path)
            if transcribed:
                final_input = transcribed
                logger.info(f"User ({user_id}) Voice: {final_input}")
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，沒聽清楚您的聲音，請再說一遍或直接打字。"))
                return

        # 生成文字回覆 (帶記憶)
        response_text = generate_text_reply(user_id, final_input)
        logger.info(f"Dr. Xiao Reply to ({user_id}): {response_text[:50]}...")
        
        # 決定是否回傳語音 (如果使用者傳語音，我們就回傳語音)
        if audio_file_path:
            local_path, audio_url = generate_voice_openai(response_text)
            if audio_url and local_path:
                audio_len = len(AudioSegment.from_mp3(local_path))
                line_bot_api.reply_message(event.reply_token, [
                    AudioSendMessage(original_content_url=audio_url, duration=audio_len),
                    TextSendMessage(text=response_text) # 同時傳文字方便閱讀
                ])
                return

        # 預設傳送文字
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

    except Exception as e:
        logger.error(f"General Error: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="系統繁忙中，請稍候重試。"))

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    msg_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as tf:
        for chunk in msg_content.iter_content(): tf.write(chunk)
        temp_path = tf.name
    try: process_and_reply(event, audio_file_path=temp_path)
    finally: 
        if os.path.exists(temp_path): os.remove(temp_path)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    process_and_reply(event, user_text=event.message.text)

if __name__ == "__main__":
    app.run(port=5005)