import asyncio
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(r"E:\Project AI\Tạo video vẽ tay").resolve()
sys.path.insert(0, str(REPO_ROOT))

from whiteboard_app.project import VideoProject, Scene, NarrationCue, _read_manifest
from whiteboard_app.timeline import compile_scene_timeline
from whiteboard_app.renderer import build_commands, subprocess_environment

import edge_tts

DRIVE_DIR = Path(r"G:\My Drive\Đăng video")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycby0n2AFHNxWRE2CXlblJuFLm9dJoBzawmonnKkLXDAugrJvZz5WHhbkmWQT6qscAe3VyA/exec"

FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segouib.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def clean_filename(s):
    s = re.sub(r'[\\/*?:"<>|#]', "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s

async def synthesize_voice_edge(text: str, output_path: Path, voice: str = "vi-VN-HoaiMyNeural"):
    """Tạo audio qua EdgeTTS và convert sang WAV PCM 16-bit 24kHz mono."""
    temp_mp3 = output_path.with_suffix(".mp3")
    comm = edge_tts.Communicate(text, voice, rate="+6%")
    await comm.save(str(temp_mp3))
    
    # Convert sang WAV 24000Hz 1 channel 16-bit
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(temp_mp3),
        "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
        str(output_path)
    ]
    subprocess.run(cmd, check=True)
    if temp_mp3.exists():
        temp_mp3.unlink()

def create_scene_image(
    output_png: Path,
    theme_color: tuple,
    banner_title: str,
    badge_text: str,
    bullet_points: list[str],
    cta_text: str
):
    """Vẽ ảnh phân cảnh dọc 1080x1920 sắc nét trên nền giấy kem #F5EBD7."""
    img = Image.new("RGB", (1080, 1920), color="#F5EBD7")
    draw = ImageDraw.Draw(img)

    # 1. Top Banner (y: 60 to 200)
    draw_rounded_rect(draw, (50, 60, 1030, 200), radius=28, fill=theme_color, outline=(255, 255, 255), width=3)
    f_banner = get_font(FONT_BOLD, 42)
    draw.text((540, 130), banner_title, font=f_banner, fill=(255, 255, 255), anchor="mm")

    # 2. Central Visual Card (y: 230 to 760)
    draw_rounded_rect(draw, (50, 230, 1030, 760), radius=32, fill=(255, 255, 255), outline=theme_color, width=4)
    # Badge inside visual card
    draw_rounded_rect(draw, (100, 260, 980, 360), radius=20, fill=theme_color)
    f_badge = get_font(FONT_BOLD, 44)
    draw.text((540, 310), badge_text, font=f_badge, fill=(255, 255, 255), anchor="mm")

    # Visual Highlight decoration inside card
    draw_rounded_rect(draw, (120, 390, 960, 730), radius=24, fill=(250, 245, 235), outline=(220, 210, 195), width=2)
    f_deco_title = get_font(FONT_BOLD, 48)
    f_deco_sub = get_font(FONT_SEGOE_BOLD, 34)
    draw.text((540, 470), "⭐ HƯỚNG DẪN CHUẨN Y KHOA", font=f_deco_title, fill=theme_color, anchor="mm")
    draw.text((540, 560), "VIỆN DINH DƯỠNG & WHO KHUYÊN DÙNG", font=f_deco_sub, fill=(100, 80, 60), anchor="mm")
    draw.text((540, 650), "An Toàn Cho Dạ Dày & Hệ Tiêu Hóa Của Bé", font=f_deco_sub, fill=(130, 110, 90), anchor="mm")

    # 3. Content Highlights (y: 790 to 1580)
    box_y = 790
    box_h = 240
    box_spacing = 25
    f_bullet_title = get_font(FONT_BOLD, 38)
    f_bullet_desc = get_font(FONT_SEGOE_BOLD, 34)

    for i, pt in enumerate(bullet_points[:3]):
        cur_y = box_y + i * (box_h + box_spacing)
        draw_rounded_rect(draw, (50, cur_y, 1030, cur_y + box_h), radius=24, fill=(255, 255, 255), outline=(200, 190, 175), width=2)
        # Left number badge
        draw_rounded_rect(draw, (80, cur_y + 30, 170, cur_y + 120), radius=16, fill=theme_color)
        f_num = get_font(FONT_BOLD, 46)
        draw.text((125, cur_y + 75), f"0{i+1}", font=f_num, fill=(255, 255, 255), anchor="mm")
        
        # Text
        parts = pt.split(":", 1)
        if len(parts) == 2:
            title_text = parts[0].strip()
            body_text = parts[1].strip()
        else:
            title_text = f"Bước {i+1}"
            body_text = pt.strip()

        draw.text((200, cur_y + 60), title_text.upper(), font=f_bullet_title, fill=theme_color, anchor="lm")
        
        # Multiline body wrapping
        words = body_text.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 34:
                lines.append(" ".join(cur_line))
                cur_line = []
        if cur_line:
            lines.append(" ".join(cur_line))
        
        for line_idx, line in enumerate(lines[:2]):
            draw.text((200, cur_y + 120 + line_idx * 48), line, font=f_bullet_desc, fill=(45, 45, 45), anchor="lm")

    # 4. Bottom CTA / Branding (y: 1610 to 1850)
    draw_rounded_rect(draw, (50, 1610, 1030, 1850), radius=28, fill=(255, 255, 255), outline=theme_color, width=3)
    f_cta_brand = get_font(FONT_BOLD, 42)
    f_cta_body = get_font(FONT_SEGOE_BOLD, 36)
    draw.text((540, 1670), "🍓 ĂN DẶM MẸ DÂU — CÙNG CON LỚN KHÔN", font=f_cta_brand, fill=theme_color, anchor="mm")
    draw.text((540, 1750), cta_text, font=f_cta_body, fill=(30, 30, 30), anchor="mm")

    output_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_png, quality=95)

    # Return annotation mapping 4 regions covering 100% elements
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "top_banner",
                "label": "Thẻ Tiêu Đề Chủ Đề",
                "region": {"x": 40, "y": 50, "width": 1000, "height": 160},
                "reveal": {"startMs": 100, "durationMs": 1500}
            },
            {
                "id": "central_card",
                "label": "Thẻ Trực Quan Trung Tâm",
                "region": {"x": 40, "y": 220, "width": 1000, "height": 550},
                "reveal": {"startMs": 1600, "durationMs": 2500}
            },
            {
                "id": "content_cards",
                "label": "Khối Kiến Thức Cốt Lõi",
                "region": {"x": 40, "y": 780, "width": 1000, "height": 810},
                "reveal": {"startMs": 4100, "durationMs": 3500}
            },
            {
                "id": "bottom_cta",
                "label": "Thương Hiệu & Kêu Gọi Hành Động",
                "region": {"x": 40, "y": 1600, "width": 1000, "height": 260},
                "reveal": {"startMs": 7600, "durationMs": 1800}
            }
        ]
    }
    return annotation

def update_google_sheets(day: int, slot_id: int, video_path: str, status: str):
    """Gửi cập nhật lên Google Sheets qua Webhook."""
    payload = {
        "action": "update_row",
        "day": day,
        "slot_id": slot_id,
        "video_path": video_path,
        "status": status
    }
    req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_text = resp.read().decode("utf-8")
            print(f"  [Sheets Webhook] Cập nhật Slot {slot_id}: {res_text}")
    except Exception as e:
        print(f"  [Sheets Webhook] Lỗi: {e}")

async def produce_slot(slot_data: dict):
    slot_id = slot_data["slot_id"]
    title = slot_data["title"]
    hook = slot_data.get("hook", "")
    body = slot_data.get("body", "")
    cta = slot_data.get("cta", "")
    clean_t = clean_filename(title)
    
    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU SẢN XUẤT: SLOT {slot_id} — {title}")
    print(f"=======================================================")

    project_dir = REPO_ROOT / "projects" / f"day_01_slot_{slot_id:02d}"
    output_dir = project_dir / "output"
    audio_dir = output_dir / "audio-scenes"
    audio_dir.mkdir(parents=True, exist_ok=True)

    PALETTES = [
        (217, 83, 79),   # Coral Red
        (230, 126, 34),  # Orange
        (46, 204, 113),  # Emerald
        (52, 152, 219),  # Dodger Blue
        (155, 89, 182),  # Amethyst Purple
        (26, 188, 156),  # Turquoise
        (243, 156, 18),  # Warm Amber
        (231, 76, 60),   # Crimson
        (41, 128, 185),  # Deep Blue
        (142, 68, 173),  # Royal Purple
        (211, 84, 0)     # Dark Orange
    ]
    theme_color = PALETTES[(slot_id - 1) % len(PALETTES)]

    body_sentences = [s.strip() for s in re.split(r"[.;\n]", body) if s.strip()]
    if len(body_sentences) < 3:
        body_sentences = [
            "Quy tắc vàng: Bắt đầu từ lượng ít đến nhiều, loãng đến đặc.",
            "Lưu ý quan trọng: Quan sát phản ứng dị ứng và tiêu hóa của con.",
            "Lời khuyên y khoa: Không nêm gia vị, tôn trọng nhu cầu tự nhiên của bé."
        ]

    scenes_spec = [
        {
            "id": "scene_01",
            "voice_text": f"Chào mẹ, {hook}",
            "banner": f"💡 {title}".upper()[:35],
            "badge": "⚠️ ĐIỀU MẸ CẦN BIẾT NGAY",
            "bullets": [
                f"Vấn đề cốt lõi: {hook[:70]}",
                "Hệ quả nếu làm sai: Bé dễ nôn trớ, khó tiêu hoặc sợ ăn",
                "Giải pháp khoa học: Áp dụng chuẩn hướng dẫn ngay sau đây"
            ],
            "cta": "Cùng Mẹ Dâu tìm hiểu giải pháp chuẩn y khoa nhé!"
        },
        {
            "id": "scene_02",
            "voice_text": f"Đây là 3 điểm cốt lõi mẹ cần nắm chắc: {body}",
            "banner": "⭐ BÍ QUYẾT ĂN DẶM CHUẨN",
            "badge": "📋 3 NGUYÊN TẮC QUAN TRỌNG",
            "bullets": [
                f"Bước 1: {body_sentences[0][:65]}",
                f"Bước 2: {body_sentences[1][:65]}",
                f"Bước 3: {body_sentences[2][:65]}"
            ],
            "cta": "Mẹ hãy lưu lại để áp dụng chuẩn xác cho con nhé!"
        },
        {
            "id": "scene_03",
            "voice_text": f"{cta}",
            "banner": "💖 LỜI KHUYÊN TỪ MẸ DÂU",
            "badge": "🎯 ĐÍCH ĐẾN HẠNH PHÚC",
            "bullets": [
                "Kiên nhẫn & Tôn trọng: Không ép ăn khi con đã quay đầu",
                "Dinh dưỡng cân bằng: Đủ nhóm chất theo từng giai đoạn",
                "Đồng hành khoa học: Cùng con khám phá ẩm thực mỗi ngày"
            ],
            "cta": "👉 Bấm Follow kênh để xem thêm bài học ăn dặm mỗi ngày!"
        }
    ]

    scene_audio_map = {}
    project_scenes = []
    project_narration = []

    for idx, sc in enumerate(scenes_spec, start=1):
        sc_id = sc["id"]
        sc_png = project_dir / f"{sc_id}.png"
        sc_ann_file = project_dir / f"{sc_id}.annotation.json"
        sc_wav = audio_dir / f"{idx:02d}-{sc_id}.wav"

        # A. Voice synthesis
        print(f"  [1/4] Tạo giọng đọc Cảnh {idx}...")
        await synthesize_voice_edge(sc["voice_text"], sc_wav, voice="vi-VN-HoaiMyNeural")
        scene_audio_map[sc_id] = sc_wav

        # B. Image & Annotation creation
        print(f"  [2/4] Thiết kế đồ họa Cảnh {idx}...")
        ann_data = create_scene_image(
            output_png=sc_png,
            theme_color=theme_color,
            banner_title=sc["banner"],
            badge_text=sc["badge"],
            bullet_points=sc["bullets"],
            cta_text=sc["cta"]
        )
        sc_ann_file.write_text(json.dumps(ann_data, ensure_ascii=False, indent=2), encoding="utf-8")
        project_scenes.append({
            "id": sc_id,
            "title": sc["banner"],
            "image": sc_png.name,
            "annotation": sc_ann_file.name
        })

        cue_id = f"cue_{idx:02d}"
        project_narration.append(NarrationCue(
            cue_id=cue_id,
            scene_id=sc_id,
            text=sc["voice_text"],
            element_ids=["top_banner", "central_card", "content_cards", "bottom_cta"],
            pause_before_ms=100
        ))

    # 2. Tạo manifest project.json
    project_manifest = {
        "schemaVersion": 1,
        "title": title,
        "aspectRatio": "9:16 2K",
        "penBrand": "Ăn dặm mẹ Dâu",
        "scenes": project_scenes,
        "narration": [
            {
                "id": c.cue_id,
                "sceneId": c.scene_id,
                "text": c.text,
                "elementIds": c.element_ids,
                "pauseBeforeMs": c.pause_before_ms
            }
            for c in project_narration
        ]
    }
    manifest_path = project_dir / "project.json"
    manifest_path.write_text(json.dumps(project_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    project = _read_manifest(manifest_path)

    # 3. Compile timeline
    print(f"  [3/4] Biên dịch Timeline & Đồng bộ Whiteboard...")
    timeline_res = compile_scene_timeline(
        project=project,
        scene_audio=scene_audio_map,
        output_dir=output_dir,
        on_log=lambda m: None
    )
    project.voice = timeline_res.voice_path
    project.runtime_annotations = timeline_res.runtime_annotations

    # 4. Build render commands and run
    print(f"  [4/4] Render video vẽ tay GPU (2K 1440x2560)...")
    commands, final_target = build_commands(
        project=project,
        output_dir=output_dir,
        aspect_ratio="9:16 2K"
    )

    env = subprocess_environment()
    for cmd_idx, cmd in enumerate(commands, start=1):
        print(f"    -> Tiến trình [{cmd_idx}/{len(commands)}]: {cmd.label}...")
        proc = subprocess.run(
            cmd.argv,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if proc.returncode != 0:
            print(f"LỖI TẠI BƯỚC: {cmd.label}")
            print(proc.stderr[:500])
            raise RuntimeError(f"Render failed at {cmd.label}")

    final_mp4 = output_dir / "final.mp4"
    if not final_mp4.is_file():
        raise RuntimeError(f"Chưa thấy file output final.mp4 tại {output_dir}")

    # 5. Export to Google Drive
    drive_dest = DRIVE_DIR / f"Day_01_Slot_{slot_id:02d}_{clean_t}_2K.mp4"
    shutil.copy2(final_mp4, drive_dest)
    print(f"  ✅ ĐÃ XUẤT FILE SANG DRIVE: {drive_dest} ({drive_dest.stat().st_size / (1024*1024):.2f} MB)")

    # 6. Update Google Sheets Webhook
    update_google_sheets(
        day=1,
        slot_id=slot_id,
        video_path=str(drive_dest),
        status="READY_TO_PUBLISH (2K 1440x2560)"
    )
    print(f"  🎉 HOÀN THÀNH XUẤT BẢN CHO SLOT {slot_id}!\n")

async def main():
    with open(REPO_ROOT / "knowledge/an_dam_me_dau/CONTENT_PLAN_30_DAYS_300_VIDEOS.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Lấy các slot từ Slot 1 đến Slot 11 của Ngày 1
    day1_slots = [x for x in data if x.get("day") == 1]
    day1_slots.sort(key=lambda x: x.get("slot_id"))

    print(f"Kiểm tra {len(day1_slots)} slot của Ngày 1:")
    
    for item in day1_slots:
        slot_id = item.get("slot_id")
        title = item.get("title")
        clean_t = clean_filename(title)
        
        # Kiểm tra xem file đã xuất hiện trong Google Drive chưa
        matches = list(DRIVE_DIR.glob(f"Day_01_Slot_{slot_id:02d}_*_2K.mp4"))
        if matches:
            print(f"⏩ Slot {slot_id} ({title}) đã tồn tại: {matches[0].name}. Bỏ qua.")
            continue
            
        try:
            await produce_slot(item)
        except Exception as e:
            print(f"❌ LỖI KHI XỬ LÝ SLOT {slot_id}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
