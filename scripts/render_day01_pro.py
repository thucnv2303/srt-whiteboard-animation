import io
import os
import sys
import subprocess
import threading
from pathlib import Path

# Force UTF-8 encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

REPO_ROOT = Path(r"E:\Project AI\Tạo video vẽ tay")
sys.path.insert(0, str(REPO_ROOT))

from whiteboard_app.project import VideoProject, _read_manifest
from whiteboard_app.voice import generate_cue_voices
from whiteboard_app.timeline import compile_timeline
from whiteboard_app.renderer import build_commands, subprocess_environment

REPO_ROOT = Path(r"E:\Project AI\Tạo video vẽ tay")
PROJECT_DIR = REPO_ROOT / "output" / "day_01_pro"
OUTPUT_DIR = PROJECT_DIR / "render"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")

def main():
    print("=== BẮT ĐẦU QUY TRÌNH SẢN XUẤT VIDEO 9:16 PRO (ĂN DẶM MẸ DÂU) ===")
    manifest_path = PROJECT_DIR / "project.json"
    project = _read_manifest(manifest_path)
    print(f"Project: {project.title}")
    print(f"Số lượng cảnh (Scenes): {len(project.scenes)}")
    print(f"Số lượng câu thoại (Cues): {len(project.narration_cues)}")

    # 1. Generate Voice Cues with Xuan Dung Profile
    print("\n--- BƯỚC 1: TẠO GIỌNG ĐỌC XUÂN DUNG (OMNIVOICE) ---")
    cues_audio_dir = OUTPUT_DIR / "cue_voices"
    cue_audio_map = generate_cue_voices(
        cli_path=CLI_PATH,
        cues=project.narration_cues,
        reference_audio=VOICE_REF,
        output_dir=cues_audio_dir,
        on_log=lambda msg: print(f"[OmniVoice] {msg}"),
        cancel_event=threading.Event(),
    )
    print("Tạo xong toàn bộ voice cues!")

    # 2. Compile Timeline & Sync Whiteboard Reveals
    print("\n--- BƯỚC 2: BIÊN DỊCH TIMELINE & ĐỒNG BỘ VẼ TAY ---")
    timeline_res = compile_timeline(
        project=project,
        cue_audio=cue_audio_map,
        output_dir=OUTPUT_DIR,
        on_log=lambda msg: print(f"[Timeline] {msg}"),
    )
    project.voice = timeline_res.voice_path
    project.runtime_annotations = timeline_res.runtime_annotations
    print(f"Audio Master: {timeline_res.voice_path} ({timeline_res.total_duration_ms/1000:.1f}s)")

    # 3. Build & Run Render Commands (9:16)
    print("\n--- BƯỚC 3: RENDER 3 CẢNH VẼ TAY 9:16 VÀ GHÉP VIDEO HOÀN CHỈNH ---")
    commands, final_target = build_commands(
        project=project,
        output_dir=OUTPUT_DIR,
        aspect_ratio="9:16",
    )

    env = subprocess_environment()
    for idx, cmd in enumerate(commands, start=1):
        print(f"\n[{idx}/{len(commands)}] {cmd.label}...")
        proc = subprocess.run(
            cmd.argv,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            print(f"LỖI TẠI BƯỚC: {cmd.label}")
            print(proc.stderr)
            sys.exit(1)
        else:
            print(f"Hoàn thành: {cmd.label}")

    final_mp4 = OUTPUT_DIR / "final.mp4"
    if final_mp4.is_file():
        size_mb = final_mp4.stat().st_size / (1024 * 1024)
        print(f"\n🎉 THÀNH CÔNG! VIDEO ĐÃ SẴN SÀNG: {final_mp4} ({size_mb:.2f} MB)")
    else:
        print(f"\n⚠️ Chưa thấy file final.mp4 tại {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
