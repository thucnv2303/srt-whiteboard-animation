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
from whiteboard_app.voice import generate_scene_voices
from whiteboard_app.timeline import compile_scene_timeline
from whiteboard_app.renderer import build_commands, subprocess_environment

PROJECT_DIR = REPO_ROOT / "projects" / "day_01_an_dam_v2"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")

def main():
    print("=== BẮT ĐẦU SẢN XUẤT VIDEO NGÀY 01 V2 (ĂN DẶM MẸ DÂU) ===")
    manifest_path = PROJECT_DIR / "project.json"
    project = _read_manifest(manifest_path)
    print(f"Project: {project.title}")
    print(f"Số lượng cảnh (Scenes): {len(project.scenes)}")
    print(f"Số lượng câu thoại (Cues): {len(project.narration_cues)}")

    # 1. Generate Scene Voices with Xuan Dung Clean Profile
    print("\n--- BƯỚC 1: TẠO GIỌNG ĐỌC XUÂN DUNG LIỀN MẠCH THEO CẢNH (OMNIVOICE CLEAN) ---")
    scenes_audio_dir = OUTPUT_DIR / "audio-scenes"
    scene_audio_map = generate_scene_voices(
        cli_path=CLI_PATH,
        project=project,
        reference_audio=VOICE_REF,
        output_dir=scenes_audio_dir,
        on_log=lambda msg: print(f"[OmniVoice] {msg}"),
        cancel_event=threading.Event(),
        reference_text="Muốn đổi món với thịt bò cho bé, đây là 5 gợi ý dễ ăn.",
    )
    print("Tạo xong 4 file voice liền mạch cho 4 cảnh!")

    # 2. Compile Timeline & Sync Whiteboard Reveals
    print("\n--- BƯỚC 2: BIÊN DỊCH TIMELINE & ĐỒNG BỘ VẼ TAY ---")
    timeline_res = compile_scene_timeline(
        project=project,
        scene_audio=scene_audio_map,
        output_dir=OUTPUT_DIR,
        on_log=lambda msg: print(f"[Timeline] {msg}"),
    )
    project.voice = timeline_res.voice_path
    project.runtime_annotations = timeline_res.runtime_annotations
    print(f"Audio Master: {timeline_res.voice_path} ({timeline_res.total_duration_ms/1000:.1f}s)")

    # 3. Build & Run Render Commands (9:16 2K 1440x2560)
    print("\n--- BƯỚC 3: RENDER 4 CẢNH VẼ TAY 9:16 2K (1440x2560) VÀ GHÉP VIDEO ---")
    commands, final_target = build_commands(
        project=project,
        output_dir=OUTPUT_DIR,
        aspect_ratio="9:16 2K",
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
        print(f"\n🎉 THÀNH CÔNG! VIDEO V2 ĐÃ SẴN SÀNG: {final_mp4} ({size_mb:.2f} MB)")
    else:
        print(f"\n⚠️ Chưa thấy file final.mp4 tại {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
