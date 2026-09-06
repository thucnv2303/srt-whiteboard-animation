#!/usr/bin/env python3
"""
Quy trình sản xuất Video Ăn Dặm Mẹ Dâu - Chuẩn Seamless Storytelling & Voice-First:
1. Kịch bản viết liền một mạch theo từng cảnh, có câu chuyển ý tự nhiên.
2. Render Voice trước bằng OmniVoice (đọc cả đoạn mượt mà, không cắt vụn).
3. Đo chính xác thời lượng Voice thực tế của từng cảnh.
4. Tự động tính toán & co giãn tốc độ vẽ nét tay (timing) của các phần tử khớp 100% với nhịp đọc.
5. Render video thần tốc với GPU Acceleration (h264_mf) và ghép MP4 hoàn chỉnh.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import time
import wave
import zipfile
from pathlib import Path

# Force UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "output" / "day_01_seamless_storytelling"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR = OUT_DIR / "render"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
VOICES_DIR = OUT_DIR / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# OmniVoice Settings
CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")
REF_TEXT = "Muốn đổi món với thịt bò cho bé, đây là 5 gợi ý dễ ăn."

# Nguồn ảnh và annotation mẫu (từ day_01_an_dam_v2)
SRC_PROJECT_DIR = REPO_ROOT / "projects" / "day_01_an_dam_v2"

# Kịch bản liền một mạch có câu nối tiếp chuyển đoạn tự nhiên
SCENES_SCRIPT = [
    {
        "scene_id": "scene_01",
        "title": "Cảnh 1: Cảnh báo quá tải thận & Dẫn nhập",
        "image": SRC_PROJECT_DIR / "scene_01.png",
        "annotation_src": SRC_PROJECT_DIR / "scene_01.annotation.json",
        "text": (
            "Nhiều mẹ thấy con vừa tròn sáu tháng là vội nấu cháo thịt bò, chim bồ câu để tẩm bổ cho con. "
            "Nhưng mẹ ơi, dừng lại ngay nhé! Vì lúc này, hai quả thận nhỏ xíu của con chưa đủ sức lọc lượng đạm đậm đặc này đâu! "
            "Và mẹ có biết vì sao lại nguy hiểm như vậy không? Hãy cùng nhìn vào bên trong dạ dày của con nhé."
        ),
        # Phân bổ tỷ lệ thời gian vẽ nét tay cho các element trong cảnh (tổng = 1.0)
        "element_weights": [
            ("s1_kidney_visual", 0.28),      # Quả thận
            ("s1_meat_danger_visual", 0.24), # Bát cháo cấm
            ("s1_top_banner", 0.16),         # Banner cảnh báo
            ("s1_alert_card", 0.32),         # Thẻ cảnh báo to
        ]
    },
    {
        "scene_id": "scene_02",
        "title": "Cảnh 2: So sánh cơ chế dạ dày sữa lỏng và đạm đặc",
        "image": SRC_PROJECT_DIR / "scene_02.png",
        "annotation_src": SRC_PROJECT_DIR / "scene_02.annotation.json",
        "text": (
            "Dạ dày của bé sáu tháng vốn chỉ quen với dòng sữa mẹ êm dịu. "
            "Nếu mẹ cho con ăn đặc quá sớm, thức ăn sẽ ứ đọng lại, làm con bị trào ngược, nôn trớ, táo bón nặng và rất dễ sợ ăn dặm kéo dài. "
            "Chính vì vậy, để con làm quen an toàn mà hào hứng, mẹ hãy áp dụng ngay lộ trình ba ngày vàng khởi động này nhé."
        ),
        "element_weights": [
            ("s2_stomach_milk_visual", 0.25),   # Dạ dày sữa lỏng
            ("s2_card_milk", 0.20),             # Thẻ chữ sữa lỏng
            ("s2_stomach_clogged_visual", 0.30),# Dạ dày ứ đọng
            ("s2_card_clogged", 0.25),          # Thẻ chữ táo bón
        ]
    },
    {
        "scene_id": "scene_03",
        "title": "Cảnh 3: Lộ trình 3 ngày vàng khởi động",
        "image": SRC_PROJECT_DIR / "scene_03.png",
        "annotation_src": SRC_PROJECT_DIR / "scene_03.annotation.json",
        "text": (
            "Ngày đầu tiên, mẹ chỉ cho con thử một thìa cháo rây loãng mịn như dòng sữa mẹ. "
            "Sang ngày thứ hai, hòa thêm chút sữa quen thuộc giúp con hào hứng hợp tác. "
            "Và đến ngày thứ ba, hãy thêm một thìa bí đỏ ngọt bùi giàu vitamin A mẹ nhé. "
            "Và để cả hành trình ăn dặm của con luôn nhẹ nhàng, mẹ chỉ cần khắc ghi ba nguyên tắc vàng sau đây."
        ),
        "element_weights": [
            ("s3_top_banner", 0.10),        # Banner 3 ngày vàng
            ("s3_bowl_day1_visual", 0.18),  # Bát Ngày 1
            ("s3_card_day1", 0.12),         # Thẻ Ngày 1
            ("s3_bowl_day2_visual", 0.18),  # Bát Ngày 2
            ("s3_card_day2", 0.12),         # Thẻ Ngày 2
            ("s3_bowl_day3_visual", 0.18),  # Bát Ngày 3
            ("s3_card_day3", 0.12),         # Thẻ Ngày 3
        ]
    },
    {
        "scene_id": "scene_04",
        "title": "Cảnh 4: 3 Nguyên tắc vàng & Kêu gọi Follow",
        "image": SRC_PROJECT_DIR / "scene_04.png",
        "annotation_src": SRC_PROJECT_DIR / "scene_04.annotation.json",
        "text": (
            "Thứ nhất là ăn từ ít đến nhiều. "
            "Thứ hai là ăn từ loãng đến đặc. "
            "Và tuyệt đối không nêm mắm muối gia vị dưới một tuổi. "
            "Mẹ hãy bấm Follow kênh Ăn dặm mẹ Dâu để cùng mẹ đồng hành suốt ba mươi ngày ăn dặm khoa học cho con nhé!"
        ),
        "element_weights": [
            ("s4_mom_baby_visual", 0.35),   # Hình mẹ con
            ("s4_rules_card", 0.35),        # Khung 3 nguyên tắc vàng
            ("s4_cta_card", 0.30),          # Thẻ kêu gọi Follow
        ]
    }
]


def get_wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as w:
        return round(w.getnframes() * 1000 / w.getframerate())


def step_1_render_seamless_voices() -> dict[str, dict]:
    print("\n" + "=" * 60)
    print("BƯỚC 1: RENDER TOÀN BỘ VOICE LIỀN MẠCH THEO TỪNG CẢNH (VOICE-FIRST)")
    print("=" * 60)
    
    manifest_file = VOICES_DIR / "cue-manifest.json"
    manifest_data = {"schemaVersion": 1, "cues": []}
    voice_files = {}

    for item in SCENES_SCRIPT:
        sid = item["scene_id"]
        out_wav = VOICES_DIR / f"{sid}.wav"
        voice_files[sid] = out_wav
        manifest_data["cues"].append({
            "id": sid,
            "text": item["text"],
            "synthesisText": item["text"].strip(),
            "output": str(out_wav)
        })

    manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    from whiteboard_app.voice import python_for_omnivoice_cli
    python_exe = python_for_omnivoice_cli(CLI_PATH)
    helper = REPO_ROOT / "scripts" / "generate_omnivoice_cues.py"
    
    cmd = [
        str(python_exe), str(helper),
        "--manifest", str(manifest_file),
        "--ref-audio", str(VOICE_REF),
        "--ref-text", REF_TEXT,
        "--language", "vi"
    ]
    print(f"Đang gọi OmniVoice tạo 4 đoạn voice liền mạch với ref-text...")
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print("Lỗi OmniVoice:", proc.stderr)
        raise RuntimeError(f"OmniVoice thất bại: {proc.stderr}")
    print(f"Tạo xong 4 đoạn voice trong {time.time() - t0:.2f}s!")

    scene_voice_info = {}
    for item in SCENES_SCRIPT:
        sid = item["scene_id"]
        wav_path = voice_files[sid]
        dur_ms = get_wav_duration_ms(wav_path)
        scene_voice_info[sid] = {
            "path": wav_path,
            "duration_ms": dur_ms,
            "text": item["text"]
        }
        print(f"  ✓ {sid}: {dur_ms} ms ({dur_ms/1000:.2f}s) | {item['text'][:60]}...")
    return scene_voice_info


def step_2_adapt_video_timing_to_voice(voice_info: dict[str, dict]):
    print("\n" + "=" * 60)
    print("BƯỚC 2: CĂN CHỈNH TỐC ĐỘ VẼ TAY THÍCH ỨNG CHÍNH XÁC VỚI THỜI LƯỢNG VOICE")
    print("=" * 60)

    adapted_annotations = {}
    for item in SCENES_SCRIPT:
        sid = item["scene_id"]
        v_dur_ms = voice_info[sid]["duration_ms"]
        
        # Đọc annotation gốc
        source_ann = json.loads(item["annotation_src"].read_text(encoding="utf-8"))
        ann = json.loads(json.dumps(source_ann)) # clone
        
        # Căn chỉnh tốc độ vẽ:
        # Dành 300ms đầu để người xem định hình khung cảnh
        # Dành 800ms cuối làm thời gian tĩnh (Gaze) sau khi giọng đọc dứt
        # Tổng thời gian vẽ nét bút = voice_duration - 300ms
        lead_in_ms = 300
        gaze_ms = 800
        total_scene_ms = v_dur_ms + gaze_ms
        ann["sceneDurationMs"] = total_scene_ms

        available_draw_ms = max(1000, v_dur_ms - lead_in_ms)
        weights = item["element_weights"]
        sum_w = sum(w for _, w in weights)

        curr_start = lead_in_ms
        element_lookup = {el["id"]: el for el in ann["elements"]}

        print(f"\n--- {sid} (Voice: {v_dur_ms/1000:.2f}s, Video: {total_scene_ms/1000:.2f}s) ---")
        for el_id, weight in weights:
            el = element_lookup.get(el_id)
            if not el:
                continue
            dur = max(600, round(available_draw_ms * (weight / sum_w)))
            el["reveal"] = {
                "startMs": curr_start,
                "durationMs": dur
            }
            print(f"  * {el.get('label', el_id)}: bắt đầu {curr_start}ms -> vẽ trong {dur}ms (kết thúc {curr_start+dur}ms)")
            curr_start += dur

        adapted_ann_path = OUT_DIR / f"{sid}.annotation.json"
        adapted_ann_path.write_text(json.dumps(ann, ensure_ascii=False, indent=2), encoding="utf-8")
        adapted_annotations[sid] = adapted_ann_path
        
        # Sao chép ảnh vào output
        shutil.copy2(item["image"], OUT_DIR / f"{sid}.png")

    return adapted_annotations


def step_3_render_scenes_with_gpu(adapted_annotations: dict[str, Path], voice_info: dict[str, dict]):
    print("\n" + "=" * 60)
    print("BƯỚC 3: DỰNG CÁC PHÂN CẢNH VỚI TỐC ĐỘ ĐÃ ĐỒNG BỘ (GPU ACCELERATED)")
    print("=" * 60)

    from scripts.render_stream_whiteboard import RegionStreamRenderer, _build_cfg, _parse_args
    from scripts.stream_render import _imread_any, transcode_h264
    hand_png = REPO_ROOT / "assets" / "drawing-hand.png"

    scene_videos = []
    for index, item in enumerate(SCENES_SCRIPT, start=1):
        sid = item["scene_id"]
        ann_path = adapted_annotations[sid]
        img_path = OUT_DIR / f"{sid}.png"
        raw_mp4 = RENDER_DIR / f"{index:02d}-{sid}_raw.mp4"
        scene_mp4 = RENDER_DIR / f"{index:02d}-{sid}.mp4"

        ann = json.loads(ann_path.read_text(encoding="utf-8"))
        total_ms = ann["sceneDurationMs"]
        img_bgr = _imread_any(str(img_path))

        cfg_args = [str(img_path), str(ann_path), str(scene_mp4), "--cap-long-edge", "1920", "--no-match-bg"]
        cfg = _build_cfg(_parse_args(cfg_args))
        
        renderer = RegionStreamRenderer(img_bgr, ann, cfg, hand_png, False, pen_brand="Ăn dặm mẹ Dâu")
        print(f"\n[Cảnh {index}/4] Đang render {sid} ({total_ms/1000:.2f}s, {round(total_ms/1000*cfg.fps)} frame @ 30FPS)...")
        
        t0 = time.time()
        renderer.render_to(raw_mp4, total_ms)
        t_draw = time.time() - t0
        
        t1 = time.time()
        transcode_h264(raw_mp4, scene_mp4)
        t_gpu = time.time() - t1

        print(f"  ✓ Xong {sid} trong {t_draw+t_gpu:.2f}s (Vẽ: {t_draw:.2f}s, GPU nén: {t_gpu:.2f}s)")
        scene_videos.append(scene_mp4)

    return scene_videos


def step_4_merge_and_mux_voice(scene_videos: list[Path], voice_info: dict[str, dict]):
    print("\n" + "=" * 60)
    print("BƯỚC 4: GHÉP CẢNH VÀ LỒNG TIẾNG HOÀN CHỈNH (CONCAT & AUDIO MUX)")
    print("=" * 60)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Không tìm thấy ffmpeg trong PATH.")

    # 1. Nối các file voice thành 1 file voice liền mạch tổng
    merged_voice_wav = RENDER_DIR / "final_voice.wav"
    voice_inputs = [str(voice_info[item["scene_id"]]["path"].resolve()) for item in SCENES_SCRIPT]
    
    # Dùng ffmpeg concat audio
    concat_list_audio = RENDER_DIR / "audio_list.txt"
    with open(concat_list_audio, "w", encoding="utf-8") as f:
        for p in voice_inputs:
            posix_p = p.replace("\\", "/")
            f.write(f"file '{posix_p}'\n")

    cmd_voice = [
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list_audio),
        "-c:a", "pcm_s16le",
        str(merged_voice_wav)
    ]
    subprocess.run(cmd_voice, check=True)
    print(f"  ✓ Đã ghép voice hoàn chỉnh: {merged_voice_wav} ({get_wav_duration_ms(merged_voice_wav)/1000:.2f}s)")

    # 2. Nối video các cảnh
    merged_video_silent = RENDER_DIR / "final_silent.mp4"
    from scripts.merge_scenes import _ffmpeg_concat_copy
    _ffmpeg_concat_copy(scene_videos, merged_video_silent)
    print(f"  ✓ Đã ghép nối các cảnh video: {merged_video_silent}")

    # 3. Mux audio với video thành final.mp4
    final_mp4 = OUT_DIR / "final_seamless.mp4"
    cmd_mux = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(merged_video_silent),
        "-i", str(merged_voice_wav),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_mp4)
    ]
    subprocess.run(cmd_mux, check=True)
    
    size_mb = final_mp4.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 60)
    print(f"🎉 XUẤT THÀNH CÔNG VIDEO SEAMLESS STORYTELLING HOÀN CHỈNH!")
    print(f"File đầu ra: {final_mp4} ({size_mb:.2f} MB)")
    print("=" * 60)
    return final_mp4


def package_project(voice_info: dict):
    # Tạo project.json
    proj = {
        "schemaVersion": 1,
        "title": "Ăn Dặm Mẹ Dâu - Ngày 01 (Seamless Storytelling)",
        "version": 1,
        "scenes": [
            {"id": "scene_01", "title": "Cảnh 1: Cảnh báo quá tải thận & Dẫn nhập", "image": "scene_01.png", "annotation": "scene_01.annotation.json"},
            {"id": "scene_02", "title": "Cảnh 2: So sánh cơ chế dạ dày sữa lỏng và đạm đặc", "image": "scene_02.png", "annotation": "scene_02.annotation.json"},
            {"id": "scene_03", "title": "Cảnh 3: Lộ trình 3 ngày vàng khởi động", "image": "scene_03.png", "annotation": "scene_03.annotation.json"},
            {"id": "scene_04", "title": "Cảnh 4: 3 Nguyên tắc vàng & Kêu gọi Follow", "image": "scene_04.png", "annotation": "scene_04.annotation.json"}
        ],
        "script": "script.txt"
    }
    (OUT_DIR / "project.json").write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Ghi script.txt liền mạch
    full_script = "\n\n".join(f"[{item['title']}]\n{item['text']}" for item in SCENES_SCRIPT)
    (OUT_DIR / "script.txt").write_text(full_script, encoding="utf-8")

    # Zip dự án để mở trong app
    zip_path = OUT_DIR / "day_01_seamless.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT_DIR / "project.json", "project.json")
        zf.write(OUT_DIR / "script.txt", "script.txt")
        for sid in ["scene_01", "scene_02", "scene_03", "scene_04"]:
            zf.write(OUT_DIR / f"{sid}.png", f"{sid}.png")
            zf.write(OUT_DIR / f"{sid}.annotation.json", f"{sid}.annotation.json")
    print(f"  ✓ Đã đóng gói dự án tại: {zip_path}")


def main():
    print("==================================================================")
    print("QUY TRÌNH MỚI: KỊCH BẢN LIỀN MẠCH + RENDER VOICE TRƯỚC + ĐỒNG BỘ TỐC ĐỘ")
    print("==================================================================")
    t_start = time.time()
    
    voice_info = step_1_render_seamless_voices()
    adapted_annotations = step_2_adapt_video_timing_to_voice(voice_info)
    scene_videos = step_3_render_scenes_with_gpu(adapted_annotations, voice_info)
    final_video = step_4_merge_and_mux_voice(scene_videos, voice_info)

    package_project(voice_info)

    total_time = time.time() - t_start
    print(f"\n⏱️ TỔNG THỜI GIAN TOÀN BỘ QUY TRÌNH: {total_time:.2f} giây ({total_time/60:.1f} phút)")


if __name__ == "__main__":
    main()
