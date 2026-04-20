import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio_folder(audio_dir=".", output_dir="knowledge_base"):
    """
    掃描資料夾內的 MP3，使用 Whisper 轉為文字並存入知識庫
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    support_extensions = ('.mp3', '.m4a', '.wav')
    
    files = [f for f in os.listdir(audio_dir) if f.endswith(support_extensions)]
    print(f"發現 {len(files)} 個音訊檔案，準備開始轉錄...")

    for filename in files:
        audio_path = os.path.join(audio_dir, filename)
        output_path = os.path.join(output_dir, f"{filename}.txt")

        # 檢查是否已經轉錄過，避免重複消費 API 額度
        if os.path.exists(output_path):
            print(f"Skipping {filename}: Transcript already exists.")
            continue

        try:
            print(f"正在轉錄: {filename}...")
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    language="zh"
                )
            
            # 在文字開頭加上星星與來源
            final_content = f"🌟 【音訊來源：{filename}】\n\n{transcript.text}"
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            
            print(f"✅ 完成: {filename}")

        except Exception as e:
            print(f"❌ 轉錄 {filename} 失敗: {e}")

if __name__ == "__main__":
    # 使用者執行前請確認已安裝 openai 套件並填寫 .env
    transcribe_audio_folder()
