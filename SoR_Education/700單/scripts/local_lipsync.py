import os
import subprocess
import sys

# 【極速口型同步引擎 V2.0 - Wav2Lip M1 Optimized】
# 基於 Wav2Lip 的本地 AI 整合腳本

WAV2LIP_DIR = "ai_engine/Wav2Lip"
CONDA_ENV_PYTHON = os.path.expanduser("~/miniforge3/envs/sadtalker/bin/python3")

def run_lipsync(source_image, drive_audio, output_file="results/output_avatar.mp4"):
    """
    呼叫 Wav2Lip 生成極速口型影片
    """
    # 確保輸出目錄存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 建立必要的 temp 目錄
    os.makedirs(os.path.join(WAV2LIP_DIR, "temp"), exist_ok=True)
    
    # 根據 M1 最佳實踐配置環境變數
    env = os.environ.copy()
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    
    # 將路徑轉為絕對路徑
    abs_source = os.path.abspath(source_image)
    abs_audio = os.path.abspath(drive_audio)
    abs_output = os.path.abspath(output_file)
    
    # 建構指令
    # checkpoints/wav2lip_gan.pth 是高品質版本
    cmd = [
        CONDA_ENV_PYTHON,
        "inference.py",
        "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
        "--face", abs_source,
        "--audio", abs_audio,
        "--outfile", abs_output,
        "--pads", "0", "10", "0", "0" # 增加下巴填充以確保口型自然
    ]
    
    print(f"⚡️ 正在啟動 Wav2Lip 極速渲染: {drive_audio}")
    try:
        subprocess.run(cmd, env=env, check=True, cwd=WAV2LIP_DIR)
        print(f"✅ 渲染完成: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Wav2Lip 渲染失敗: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python local_lipsync.py <image_path> <audio_path> [output_path]")
    else:
        out = sys.argv[3] if len(sys.argv) > 3 else "results/output_avatar.mp4"
        run_lipsync(sys.argv[1], sys.argv[2], out)
