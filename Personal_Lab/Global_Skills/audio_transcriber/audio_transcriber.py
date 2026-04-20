"""
Global_Skills / audio_transcriber
===================================
功能：處理音訊檔轉文字（Whisper），自動處理超過 24MB 的大檔案。

用法：
    from Global_Skills.audio_transcriber.audio_transcriber import transcribe_audio

    text = transcribe_audio("觀念01_xxx.mp3")
    if text:
        print(text)

需求：
    pip install openai pydub
    設定環境變數 OPENAI_API_KEY
"""

import os
from openai import OpenAI
from pydub import AudioSegment

# ─── API 設定 ─────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ 請設定環境變數 OPENAI_API_KEY")
        _client = OpenAI(api_key=api_key)
    return _client

# ─── 主要函式 ─────────────────────────────────────

def transcribe_audio(file_path: str, language: str = "zh") -> str | None:
    """
    將音訊檔轉成文字。
    - 檔案 < 24MB：直接送 Whisper
    - 檔案 >= 24MB：自動切成 15 分鐘一段，逐段聽寫後合併

    參數：
        file_path  : 音訊檔路徑（支援 mp3, m4a, wav 等）
        language   : 語言代碼，預設 "zh"（中文）

    回傳：
        完整逐字稿字串，失敗回傳 None
    """
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return None

    client = _get_client()
    file_size = os.path.getsize(file_path)
    limit_bytes = 24 * 1024 * 1024  # 24 MB

    # ── 情況 A：小檔案，直接轉錄 ──────────────────
    if file_size < limit_bytes:
        print(f"   🎤 聽寫中（{file_size/1024/1024:.1f} MB）...")
        try:
            with open(file_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="whisper-1", file=f, language=language
                )
            return result.text
        except Exception as e:
            print(f"   ❌ 聽寫失敗：{e}")
            return None

    # ── 情況 B：大檔案，切割後逐段轉錄 ─────────────
    print(f"   ⚠️ 檔案過大（{file_size/1024/1024:.1f} MB），啟動自動切割模式...")

    try:
        # 載入音訊
        ext = os.path.splitext(file_path)[1].lower().strip(".")
        audio = AudioSegment.from_file(file_path, format=ext if ext != "mp3" else "mp3")

        chunk_ms = 15 * 60 * 1000  # 15 分鐘
        chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]

        # 暫存資料夾
        temp_dir = os.path.join(os.path.dirname(file_path), "_temp_chunks")
        os.makedirs(temp_dir, exist_ok=True)

        print(f"   🔪 切成 {len(chunks)} 段，逐段聽寫...")
        full_text = ""

        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
            chunk.export(chunk_path, format="mp3", bitrate="64k")
            print(f"      第 {i+1}/{len(chunks)} 段...")

            with open(chunk_path, "rb") as f:
                res = client.audio.transcriptions.create(
                    model="whisper-1", file=f, language=language
                )
                full_text += res.text + " "

            os.remove(chunk_path)  # 即時清理

        # 清理暫存資料夾
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass  # 資料夾非空時不強制刪除

        print("   ✅ 長音訊完整聽寫完成！")
        return full_text.strip()

    except Exception as e:
        print(f"   ❌ 切割處理失敗：{e}")
        return None


def save_transcript(audio_path: str, transcript: str) -> str | None:
    """
    將逐字稿存成同名 .txt 檔。

    回傳：
        已存檔的 .txt 路徑，失敗回傳 None
    """
    txt_path = os.path.splitext(audio_path)[0] + ".txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        print(f"   📝 逐字稿已存檔：{os.path.basename(txt_path)}")
        return txt_path
    except Exception as e:
        print(f"   ❌ 存檔失敗：{e}")
        return None


def get_or_transcribe(audio_path: str, language: str = "zh") -> str | None:
    """
    優先讀取已存在的 .txt 逐字稿；若不存在才呼叫 Whisper。
    （節省 API 費用）

    回傳：
        逐字稿文字，失敗回傳 None
    """
    txt_path = os.path.splitext(audio_path)[0] + ".txt"
    if os.path.exists(txt_path):
        print(f"   ⏭️  已有逐字稿，直接讀取：{os.path.basename(txt_path)}")
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()

    text = transcribe_audio(audio_path, language)
    if text:
        save_transcript(audio_path, text)
    return text
