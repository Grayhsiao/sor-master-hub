import os
from huggingface_hub import hf_hub_download

# 定義要下載的文件列表和目的地
models = [
    {"repo_id": "vinthony/SadTalker", "filename": "auido2exp_00300-model.pth", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "auido2pose_00140-model.pth", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "epoch_20.pth", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "face_alignment_3d68.pth", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "mapping_00109-model.pth", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "mapping_00229-model.pth", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "SadTalker_V0.0.2_256.safetensors", "local_dir": "ai_engine/SadTalker/checkpoints"},
    {"repo_id": "vinthony/SadTalker", "filename": "parsing_parsenet.pth", "local_dir": "ai_engine/SadTalker/gfpgan/weights"},
    {"repo_id": "vinthony/SadTalker", "filename": "alignment_WFLW_4pt.pth", "local_dir": "ai_engine/SadTalker/gfpgan/weights"},
    {"repo_id": "vinthony/SadTalker", "filename": "GFPGANv1.4.pth", "local_dir": "ai_engine/SadTalker/gfpgan/weights"},
]

print("🚀 使用 Hugging Face Hub 下載模型權重...")

for m in models:
    dest_path = os.path.join(m["local_dir"], m["filename"])
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000: # 略過已存在且非損毀的文件
        print(f"✅ {m['filename']} 已存在且大小正常，跳過。")
        continue

    print(f"⬇️ 正在下載 {m['filename']}...")
    try:
        hf_hub_download(
            repo_id=m["repo_id"],
            filename=m["filename"],
            local_dir=m["local_dir"],
            local_dir_use_symlinks=False
        )
    except Exception as e:
        print(f"❌ 下載 {m['filename']} 失敗: {e}")

print("✨ 所有權重下載流程完成！")
