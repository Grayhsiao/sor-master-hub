"""
SoR AI Tutor Engine (gemini_tutor.py)
======================================
核心 AI 功能模組，封裝所有 Gemini API 呼叫。
使用 google-generativeai SDK 實作。
"""

import os
import json
import base64
import re
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "../../.env"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 初始化 Gemini SDK
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # 使用 1.5 Flash 作為預設模型，速度快且支援多模態
    model_flash = genai.GenerativeModel('gemini-flash-latest')
    model_pro = genai.GenerativeModel('gemini-flash-latest')
else:
    model_flash = None
    model_pro = None

# ── 科目配置 ──────────────────────────────────────────────────────────────────

SUBJECT_CONFIG = {
    "math_7": {
        "name": "七年級數學",
        "topics": ["整數與數線", "分數與比例", "一元一次方程式", "平面圖形", "統計與圖表"],
        "grading_style": "數學",
    },
    "math_8": {
        "name": "八年級數學",
        "topics": ["二次方程式", "勾股定理", "平行與截線", "機率", "多項式"],
        "grading_style": "數學",
    },
    "math_9": {
        "name": "九年級數學",
        "topics": ["二次函數", "圓的性質", "相似形", "三角函數入門", "統計"],
        "grading_style": "數學",
    },
    "science_7": {
        "name": "七年級自然",
        "topics": ["生物細胞", "物質與變化", "力與運動基礎", "地球科學入門"],
        "grading_style": "理科",
    },
    "physics_8": {
        "name": "八年級物理",
        "topics": ["速度與加速度", "力的合成", "浮力", "熱學", "光學"],
        "grading_style": "理科",
    },
    "chemistry_8": {
        "name": "八年級化學",
        "topics": ["原子結構", "化學方程式", "酸鹼鹽", "氧化還原", "莫耳概念"],
        "grading_style": "理科",
    },
}


# ── 工具函數 ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | list | None:
    """從文字中安全提取 JSON。"""
    if not text:
        return None
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    json_str = match.group(1) if match else text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        start = json_str.find("{")
        end = json_str.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(json_str[start:end+1])
            except:
                pass
        start = json_str.find("[")
        end = json_str.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(json_str[start:end+1])
            except:
                pass
    return None


# ── 主要功能 ───────────────────────────────────────────────────────────────────

def generate_questions(
    subject_key: str,
    difficulty: int = 1,
    count: int = 5,
    weak_points: list[str] | None = None,
    custom_topic: str = ""
) -> dict:
    """出題函數。"""
    if not model_flash:
        return {"error": "API Key 未設定"}

    config = SUBJECT_CONFIG.get(subject_key, SUBJECT_CONFIG["math_7"])
    difficulty_map = {1: "基礎", 2: "進階", 3: "挑戰"}
    diff_desc = difficulty_map.get(difficulty, "基礎")
    
    weak_str = "（無）"
    if weak_points:
        weak_str = "、".join(weak_points[:5])
    
    topic_str = f"指定單元：{custom_topic}" if custom_topic else f"可從以下單元選擇：{'、'.join(config['topics'])}"
    
    diff_guide = {
        1: "基礎題：整數運算為主，不含分數或複雜比例，數字在 1~50 之間，步驟不超過 3 步",
        2: "進階題：可含分數或簡單方程式，計算過程 3~5 步",
        3: "挑戰題：需要多步驟推導或綜合概念，貼近會考難度"
    }

    prompt = f"""你是一位台灣{config['name']}老師。請出 {count} 道練習題。

【絕對禁止】：
- 禁止使用任何 LaTeX 語法（不可出現 $、\\、^{{}}、_{{}} 等符號）
- 禁止使用英文字母當變數（一律用中文說明，或用 x 直接書寫不加 $ 符號）
- 題目長度控制在 40 字以內

【要求】：
- 科目：{config['name']}
- 難度規範：{diff_guide.get(difficulty, diff_guide[1])}
- {topic_str}
- 弱點補強：{weak_str}
- 題目直接寫成一句完整問句，例如：「解方程式 3x + 8 = 23，求 x 的值。」

請嚴格以 JSON 格式回傳：
{{
  "subject": "{config['name']}",
  "questions": [
    {{
      "id": 1,
      "question": "題目（純文字，無 LaTeX）",
      "answer": "正確答案（純文字）",
      "key_steps": ["步驟一（純文字）", "步驟二（純文字）"],
      "difficulty": {difficulty},
      "topic": "單元名稱"
    }}
  ]
}}"""

    try:
        response = model_flash.generate_content(prompt)
        result = _extract_json(response.text)
        if result and "questions" in result:
            return result
    except Exception as e:
        print(f"[GeminiTutor] 出題錯誤: {e}")
    
    return {"subject": config["name"], "questions": [], "error": "AI 出題失敗"}


def grade_answer(
    image_base64: str,
    question: str,
    correct_answer: str,
    key_steps: list[str],
    attempt_count: int = 1,
    subject_style: str = "數學"
) -> dict:
    """蘇格拉底式批改（分析手寫照片）。"""
    if not model_pro:
        return {"is_correct": False, "hint": "API 未就緒"}

    steps_str = "\n".join([f"步驟{i+1}：{s}" for i, s in enumerate(key_steps)])
    
    hint_instruction = "提示強度：輕微引導"
    if attempt_count == 2:
        hint_instruction = "提示強度：中等引導"
    elif attempt_count >= 3:
        hint_instruction = "提示強度：強引導，接近答案但讓學生填最後一格"

    prompt = f"""你是一位台灣{subject_style}老師，正在批改手寫作業照片。
【題目】{question}
【正確解法】{steps_str}
【批改規則】
1. 辨識學生手寫答案並判斷正確性
2. 指出哪個步驟出錯，但「絕對禁止直接說出正確答案」
3. 提供蘇格拉底式引導提示，{hint_instruction}
4. 所有回覆用純中文，禁止使用 LaTeX（禁止 $ 符號）
5. hint 和 encouragement 控制在 50 字以內

請以 JSON 格式回傳：
{{
  "is_correct": true or false,
  "score": 0到100的數字,
  "recognized_answer": "辨識到的學生答案",
  "error_step": "哪個步驟出錯（若答對填空字串）",
  "hint": "引導提示（不說答案）",
  "encouragement": "一句鼓勵語"
}}"""

    try:
        img_data = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_data))
        
        response = model_pro.generate_content([prompt, img])
        result = _extract_json(response.text)
        if result:
            result["attempt_count"] = attempt_count
            return result
    except Exception as e:
        print(f"[GeminiTutor] 批改錯誤: {e}")
    
    return {"is_correct": False, "score": 0, "hint": "批改失敗", "attempt_count": attempt_count}


def grade_answer_text(
    student_answer: str,
    question: str,
    correct_answer: str,
    key_steps: list[str],
    attempt_count: int = 1,
    subject_style: str = "數學"
) -> dict:
    """文字版批改。"""
    if not model_flash:
        return {"is_correct": False, "hint": "API 未就緒"}

    steps_str = "\n".join([f"步驟{i+1}：{s}" for i, s in enumerate(key_steps)])
    
    hint_level = ["輕微引導，只問一個反思問題", "中等引導，指出錯誤環節", "強引導，幾乎點破但讓學生自己填最後答案"][min(attempt_count-1, 2)]

    prompt = f"""你是一位台灣{subject_style}老師。
【題目】{question}
【正確解法】{steps_str}
【學生答案】{student_answer}
【這是第 {attempt_count} 次嘗試，引導強度】{hint_level}

批改規則：
1. 比對學生答案與正確解法，判斷對錯
2. 「絕對禁止直接說出正確答案」
3. hint 和 encouragement 用純中文，禁止 LaTeX（禁止 $ 符號），每句控制在 40 字以內

請以 JSON 格式回傳：
{{
  "is_correct": true or false,
  "score": 0到100的數字,
  "recognized_answer": "{student_answer}",
  "error_step": "哪個步驟出錯（若答對填空字串）",
  "hint": "引導提示（不說答案，40字內）",
  "encouragement": "一句鼓勵語（20字內）"
}}"""

    try:
        response = model_flash.generate_content(prompt)
        result = _extract_json(response.text)
        if result:
            result["attempt_count"] = attempt_count
            return result
    except Exception as e:
        print(f"[GeminiTutor] 文字批改錯誤: {e}")
    
    return {"is_correct": False, "score": 0, "hint": "批改失敗", "attempt_count": attempt_count}


def generate_explanation(
    question: str,
    correct_answer: str,
    key_steps: list[str],
    subject_style: str = "數學",
    student_error: str = ""
) -> dict:
    """第三層：完整講解。"""
    if not model_pro:
        return {"full_explanation": "API 未就緒"}

    steps_str = "\n".join([f"步驟{i+1}：{s}" for i, s in enumerate(key_steps)])
    
    prompt = f"""你是一位台灣{subject_style}老師。學生嘗試三次失敗，請完整講解這道題。
【題目】{question}
【正確答案】{correct_answer}
【正確步驟】
{steps_str}

要求：
- 用純中文說明，禁止使用 LaTeX（禁止 $ 符號）
- 步驟清晰，一步一行，每行不超過 30 字
- 語氣友善，像在跟國中生說話

請回傳 JSON：
{{
  "full_explanation": "純文字完整解題過程（用換行分隔步驟）",
  "key_concept": "這題的核心概念一句話",
  "common_mistakes": "學生常見錯誤一句話",
  "similar_example": "一道類似的練習題（含答案）"
}}"""

    try:
        response = model_pro.generate_content(prompt)
        result = _extract_json(response.text)
        if result:
            return result
    except Exception as e:
        print(f"[GeminiTutor] 講解錯誤: {e}")
    
    return {"full_explanation": "生成講解失敗"}

def analyze_weak_points(answer_history: list[dict]) -> list[str]:
    """分析弱點。"""
    wrong = [h for h in answer_history if not h.get("is_correct", True)]
    if not wrong: return []
    topics = {}
    for item in wrong:
        t = item.get("topic", "未知")
        topics[t] = topics.get(t, 0) + 1
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in sorted_topics[:5]]
