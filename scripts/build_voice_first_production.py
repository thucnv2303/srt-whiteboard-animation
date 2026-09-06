import io
import os
import sys
import json
import wave
import shutil
import subprocess
import threading
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Force UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

REPO_ROOT = Path(r"E:\Project AI\Tạo video vẽ tay")
sys.path.insert(0, str(REPO_ROOT))

BRAIN_DIR = Path(r"C:\Users\thucn\.gemini\antigravity\brain\6b62f1b5-8a13-4b72-9245-d5dbac653c8d")
OUT_DIR = REPO_ROOT / "output" / "day_01_voice_first"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR = OUT_DIR / "render"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
CUES_DIR = RENDER_DIR / "cue_voices"
CUES_DIR.mkdir(parents=True, exist_ok=True)

# Image sources
IMG1_SRC = BRAIN_DIR / "s1_kidney_warning_v2_1788505424553.jpg"
IMG2_SRC = BRAIN_DIR / "s2_stomach_compare_v2_1788505444073.jpg"
IMG3_SRC = BRAIN_DIR / "s3_golden_steps_v2_1788505463380.jpg"
IMG4_SRC = BRAIN_DIR / "s4_happy_feeding_v2_1788505528006.jpg"

# Voice CLI & Reference
CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")

# Fonts
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

def get_wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as w:
        return round(w.getnframes() * 1000 / w.getframerate())

# ==============================================================================
# BƯỚC 1: ĐỊNH NGHĨA KỊCH BẢN LIỀN MẠCH (SEAMLESS STORYTELLING SCRIPT)
# ==============================================================================
SCRIPT_DATA = [
    {
        "cue_id": "cue_01",
        "scene_id": "scene_01",
        "text": "Nhiều mẹ thấy con vừa tròn sáu tháng là vội nấu cháo thịt bò, chim bồ câu để tẩm bổ. Nhưng mẹ ơi, dừng lại ngay nhé! Vì lúc này, hai quả thận nhỏ xíu của con chưa đủ sức lọc lượng đạm đậm đặc này đâu!",
        "elements": ["s1_kidney_visual", "s1_meat_danger_visual", "s1_top_banner", "s1_alert_card"],
    },
    {
        "cue_id": "cue_02",
        "scene_id": "scene_02",
        "text": "Mẹ hãy nhìn xem, dạ dày của bé sáu tháng vốn chỉ quen với dòng sữa mẹ êm dịu.",
        "elements": ["s2_stomach_milk_visual", "s2_card_milk"],
    },
    {
        "cue_id": "cue_03",
        "scene_id": "scene_02",
        "text": "Nếu mẹ cho ăn đặc quá sớm, thức ăn sẽ ứ đọng lại, làm con bị trào ngược, nôn trớ, táo bón và sợ ăn dặm đấy ạ!",
        "elements": ["s2_stomach_clogged_visual", "s2_card_clogged"],
    },
    {
        "cue_id": "cue_04",
        "scene_id": "scene_03",
        "text": "Thế nên, thực đơn hoàn hảo nhất cho ba ngày đầu tiên sẽ là:",
        "elements": ["s3_top_banner"],
    },
    {
        "cue_id": "cue_05",
        "scene_id": "scene_03",
        "text": "Ngày đầu, mẹ chỉ cho con thử một thìa cháo rây loãng mịn như dòng sữa mẹ.",
        "elements": ["s3_bowl_day1_visual", "s3_card_day1"],
    },
    {
        "cue_id": "cue_06",
        "scene_id": "scene_03",
        "text": "Ngày thứ hai, hòa thêm chút sữa quen thuộc giúp con hào hứng hợp tác.",
        "elements": ["s3_bowl_day2_visual", "s3_card_day2"],
    },
    {
        "cue_id": "cue_07",
        "scene_id": "scene_03",
        "text": "Và sang ngày thứ ba, thêm một thìa bí đỏ ngọt bùi giàu vitamin A nhé!",
        "elements": ["s3_bowl_day3_visual", "s3_card_day3"],
    },
    {
        "cue_id": "cue_08",
        "scene_id": "scene_04",
        "text": "Mẹ cứ nhớ quy tắc vàng: Ăn từ ít đến nhiều, từ loãng đến đặc và tuyệt đối không nêm mắm muối gia vị dưới một tuổi!",
        "elements": ["s4_mom_baby_visual", "s4_rules_card"],
    },
    {
        "cue_id": "cue_09",
        "scene_id": "scene_04",
        "text": "Hãy bấm Follow kênh Ăn dặm mẹ Dâu để cùng mẹ đồng hành suốt ba mươi ngày ăn dặm khoa học của con nhé!",
        "elements": ["s4_cta_card"],
    },
]

# ==============================================================================
# BƯỚC 2: RENDER VOICE HOÀN TOÀN TRƯỚC (VOICE-FIRST SYNTHESIS)
# ==============================================================================
def render_all_voices() -> dict[str, dict]:
    print("\n--- [BƯỚC 1/4] RENDER VOICE TRƯỚC VỚI OMNIVOICE (VOICE-FIRST) ---")
    manifest = CUES_DIR / "cue-manifest.json"
    cue_paths = {}
    
    manifest_data = {
        "schemaVersion": 1,
        "cues": []
    }
    for item in SCRIPT_DATA:
        out_wav = CUES_DIR / f"{item['cue_id']}.wav"
        cue_paths[item["cue_id"]] = out_wav
        manifest_data["cues"].append({
            "id": item["cue_id"],
            "text": item["text"],
            "synthesisText": item["text"].strip(),
            "output": str(out_wav)
        })
    manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    from whiteboard_app.voice import python_for_omnivoice_cli
    python_exe = python_for_omnivoice_cli(CLI_PATH)
    helper = REPO_ROOT / "scripts" / "generate_omnivoice_cues.py"
    cmd = [
        str(python_exe), str(helper),
        "--manifest", str(manifest),
        "--ref-audio", str(VOICE_REF),
        "--language", "vi"
    ]
    print("Đang tổng hợp 9 câu voice tự nhiên...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print("Lỗi OmniVoice:", proc.stderr)
        sys.exit(1)
    print("Tổng hợp xong toàn bộ 9 câu voice!")

    voice_info = {}
    for item in SCRIPT_DATA:
        cid = item["cue_id"]
        wav_path = cue_paths[cid]
        dur_ms = get_wav_duration_ms(wav_path)
        voice_info[cid] = {
            "path": wav_path,
            "duration_ms": dur_ms,
            "text": item["text"]
        }
        print(f" * {cid}: {dur_ms} ms ({dur_ms/1000:.2f}s) -> {item['text'][:45]}...")
    return voice_info

# ==============================================================================
# BƯỚC 3: THIẾT KẾ ĐỒ HỌA CHỮ TO, RÕ RÀNG TRÊN 9:16 (HIGH CONTRAST KEYWORDS)
# ==============================================================================
def compose_scenes():
    print("\n--- [BƯỚC 2/4] DỰNG ĐỒ HỌA INFOGRAPHIC CHỮ TO, CÔ ĐỌNG (9:16) ---")
    
    # --- SCENE 1 ---
    img1 = Image.open(IMG1_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    d1 = ImageDraw.Draw(img1)
    # Banner trên cực to
    draw_rounded_rect(d1, (50, 60, 1030, 200), radius=28, fill=(220, 38, 38, 250), outline=(255, 255, 255), width=4)
    d1.text((540, 130), "🚨 CẢNH BÁO BÉ 6 THÁNG", font=get_font(FONT_BOLD, 56), fill=(255, 255, 255), anchor="mm")
    
    # Thẻ dưới từ khóa to, tương phản cao
    draw_rounded_rect(d1, (50, 1420, 1030, 1850), radius=28, fill=(255, 255, 255, 250), outline=(220, 38, 38), width=4)
    d1.text((100, 1490), "❌ CHỚ ĂN ĐẠM SỚM!", font=get_font(FONT_BOLD, 54), fill=(220, 38, 38), anchor="lm")
    d1.text((100, 1580), "⚠️ QUÁ TẢI THẬN NON NỚT", font=get_font(FONT_BOLD, 46), fill=(217, 119, 6), anchor="lm")
    d1.text((100, 1670), "• Con dễ nôn trớ & táo bón nặng", font=get_font(FONT_SEGOE_BOLD, 42), fill=(31, 41, 55), anchor="lm")
    d1.text((100, 1760), "• Nguy cơ sợ ăn dặm kéo dài!", font=get_font(FONT_BOLD, 44), fill=(185, 28, 28), anchor="lm")
    img1.convert("RGB").save(OUT_DIR / "scene_01.png", quality=95)

    # --- SCENE 2 ---
    img2 = Image.open(IMG2_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    d2 = ImageDraw.Draw(img2)
    # Thẻ trên: Sữa lỏng
    draw_rounded_rect(d2, (50, 780, 1030, 930), radius=24, fill=(255, 255, 255, 250), outline=(16, 185, 129), width=4)
    d2.text((100, 835), "✅ DẠ DÀY CHỈ QUEN SỮA LỎNG", font=get_font(FONT_BOLD, 48), fill=(5, 150, 105), anchor="lm")
    d2.text((100, 885), "• Tiêu hóa êm ái, trơn tru", font=get_font(FONT_SEGOE_BOLD, 38), fill=(75, 85, 99), anchor="lm")
    
    # Thẻ dưới: Đạm đặc
    draw_rounded_rect(d2, (50, 1680, 1030, 1850), radius=24, fill=(255, 255, 255, 250), outline=(220, 38, 38), width=4)
    d2.text((100, 1735), "❌ ĂN ĐẶC SỚM: TÁO BÓN & NÔN TRỚ!", font=get_font(FONT_BOLD, 46), fill=(220, 38, 38), anchor="lm")
    d2.text((100, 1795), "• Gây ứ đọng và quá tải dạ dày con", font=get_font(FONT_SEGOE_BOLD, 38), fill=(185, 28, 28), anchor="lm")
    img2.convert("RGB").save(OUT_DIR / "scene_02.png", quality=95)

    # --- SCENE 3 ---
    img3 = Image.open(IMG3_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    d3 = ImageDraw.Draw(img3)
    # Header Banner
    draw_rounded_rect(d3, (50, 40, 1030, 145), radius=24, fill=(16, 185, 129, 250), outline=(255, 255, 255), width=3)
    d3.text((540, 92), "🌟 3 NGÀY VÀNG KHỞI ĐỘNG", font=get_font(FONT_BOLD, 52), fill=(255, 255, 255), anchor="mm")
    
    # Card 1
    draw_rounded_rect(d3, (550, 200, 1040, 450), radius=20, fill=(255, 255, 255, 245), outline=(59, 130, 246), width=4)
    d3.text((580, 260), "NGÀY 1", font=get_font(FONT_BOLD, 40), fill=(29, 78, 216), anchor="lm")
    d3.text((580, 330), "Cháo rây 1:10 loãng mịn", font=get_font(FONT_BOLD, 38), fill=(31, 41, 55), anchor="lm")
    d3.text((580, 395), "• Khởi động 1-2 thìa nhỏ", font=get_font(FONT_SEGOE_BOLD, 34), fill=(75, 85, 99), anchor="lm")

    # Card 2
    draw_rounded_rect(d3, (550, 750, 1040, 1000), radius=20, fill=(255, 255, 255, 245), outline=(16, 185, 129), width=4)
    d3.text((580, 810), "NGÀY 2", font=get_font(FONT_BOLD, 40), fill=(4, 120, 87), anchor="lm")
    d3.text((580, 880), "Cháo trộn sữa mẹ", font=get_font(FONT_BOLD, 38), fill=(31, 41, 55), anchor="lm")
    d3.text((580, 945), "• Vị quen thuộc giúp con hợp tác", font=get_font(FONT_SEGOE_BOLD, 34), fill=(75, 85, 99), anchor="lm")

    # Card 3
    draw_rounded_rect(d3, (550, 1350, 1040, 1600), radius=20, fill=(255, 255, 255, 245), outline=(249, 115, 22), width=4)
    d3.text((580, 1410), "NGÀY 3", font=get_font(FONT_BOLD, 40), fill=(194, 65, 12), anchor="lm")
    d3.text((580, 1480), "Thêm 1 thìa bí đỏ rây", font=get_font(FONT_BOLD, 38), fill=(31, 41, 55), anchor="lm")
    d3.text((580, 1545), "• Bổ sung Vitamin A & chất xơ", font=get_font(FONT_SEGOE_BOLD, 34), fill=(75, 85, 99), anchor="lm")
    img3.convert("RGB").save(OUT_DIR / "scene_03.png", quality=95)

    # --- SCENE 4 ---
    img4 = Image.open(IMG4_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    d4 = ImageDraw.Draw(img4)
    # Khung nguyên tắc vàng
    draw_rounded_rect(d4, (50, 60, 1030, 480), radius=28, fill=(255, 255, 255, 250), outline=(147, 51, 234), width=4)
    d4.text((100, 120), "💡 3 NGUYÊN TẮC VÀNG:", font=get_font(FONT_BOLD, 48), fill=(126, 34, 206), anchor="lm")
    d4.text((100, 200), "1. ĂN TỪ ÍT ĐẾN NHIỀU (1 thìa ➡️ nửa bát)", font=get_font(FONT_BOLD, 42), fill=(31, 41, 55), anchor="lm")
    d4.text((100, 280), "2. ĂN TỪ LOÃNG ĐẾN ĐẶC (tập nuốt trơn)", font=get_font(FONT_BOLD, 42), fill=(31, 41, 55), anchor="lm")
    d4.text((100, 360), "3. TUYỆT ĐỐI KHÔNG NÊM GIA VỊ!", font=get_font(FONT_BOLD, 44), fill=(220, 38, 38), anchor="lm")
    d4.text((100, 425), "(Không mắm, muối, đường dưới 1 tuổi)", font=get_font(FONT_SEGOE_BOLD, 34), fill=(107, 114, 128), anchor="lm")

    # CTA Button
    draw_rounded_rect(d4, (50, 1600, 1030, 1850), radius=28, fill=(236, 72, 153, 250), outline=(255, 255, 255), width=4)
    d4.text((540, 1665), "ĂN DẶM MẸ DÂU", font=get_font(FONT_BOLD, 52), fill=(255, 255, 255), anchor="mm")
    d4.text((540, 1740), "❤️ BẤM FOLLOW ĐỂ XEM TIẾP NGÀY 2!", font=get_font(FONT_BOLD, 44), fill=(255, 255, 255), anchor="mm")
    d4.text((540, 1800), "Trọn bộ 30 ngày thực đơn khoa học cho bé", font=get_font(FONT_SEGOE_BOLD, 34), fill=(255, 241, 242), anchor="mm")
    img4.convert("RGB").save(OUT_DIR / "scene_04.png", quality=95)
    print("Dựng xong 4 ảnh infographic chuẩn 9:16!")

# ==============================================================================
# BƯỚC 4: TẠO ANNOTATION VÀ PROJECT.JSON ĐỒNG BỘ 100% THEO THỜI LƯỢNG VOICE
# ==============================================================================
def build_synced_project(voice_info: dict):
    print("\n--- [BƯỚC 3/4] ĐỒNG BỘ TIMELINE VẼ TAY KHỚP VỚI TỐC ĐỘ VOICE ---")
    
    # Scene 1 Annotation
    ann1 = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {"id": "s1_kidney_visual", "label": "Hình Quả Thận", "region": {"x": 40, "y": 200, "width": 550, "height": 1180}, "reveal": {"startMs": 300, "durationMs": 2500}},
            {"id": "s1_meat_danger_visual", "label": "Hình Bát Cháo Cấm", "region": {"x": 580, "y": 380, "width": 460, "height": 980}, "reveal": {"startMs": 2900, "durationMs": 2200}},
            {"id": "s1_top_banner", "label": "Banner Cảnh Báo", "region": {"x": 50, "y": 60, "width": 980, "height": 140}, "reveal": {"startMs": 5200, "durationMs": 1500}},
            {"id": "s1_alert_card", "label": "Thẻ Cảnh Báo Chữ To", "region": {"x": 50, "y": 1420, "width": 980, "height": 430}, "reveal": {"startMs": 6800, "durationMs": 2600}}
        ]
    }
    (OUT_DIR / "scene_01.annotation.json").write_text(json.dumps(ann1, ensure_ascii=False, indent=2), encoding="utf-8")

    # Scene 2 Annotation
    ann2 = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {"id": "s2_stomach_milk_visual", "label": "Hình Dạ Dày Sữa Lỏng", "region": {"x": 100, "y": 180, "width": 880, "height": 580}, "reveal": {"startMs": 300, "durationMs": 2400}},
            {"id": "s2_card_milk", "label": "Thẻ Chữ Sữa Lỏng", "region": {"x": 50, "y": 780, "width": 980, "height": 150}, "reveal": {"startMs": 2800, "durationMs": 1600}},
            {"id": "s2_stomach_clogged_visual", "label": "Hình Dạ Dày Quá Tải", "region": {"x": 100, "y": 980, "width": 880, "height": 680}, "reveal": {"startMs": 4600, "durationMs": 2600}},
            {"id": "s2_card_clogged", "label": "Thẻ Chữ Quá Tải", "region": {"x": 50, "y": 1680, "width": 980, "height": 170}, "reveal": {"startMs": 7300, "durationMs": 1800}}
        ]
    }
    (OUT_DIR / "scene_02.annotation.json").write_text(json.dumps(ann2, ensure_ascii=False, indent=2), encoding="utf-8")

    # Scene 3 Annotation
    ann3 = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {"id": "s3_top_banner", "label": "Banner 3 Ngày Vàng", "region": {"x": 50, "y": 40, "width": 980, "height": 105}, "reveal": {"startMs": 200, "durationMs": 1000}},
            {"id": "s3_bowl_day1_visual", "label": "Hình Bát Ngày 1", "region": {"x": 50, "y": 160, "width": 500, "height": 500}, "reveal": {"startMs": 1300, "durationMs": 2000}},
            {"id": "s3_card_day1", "label": "Thẻ Ngày 1", "region": {"x": 550, "y": 200, "width": 490, "height": 250}, "reveal": {"startMs": 3400, "durationMs": 1600}},
            {"id": "s3_bowl_day2_visual", "label": "Hình Bát Ngày 2", "region": {"x": 50, "y": 700, "width": 500, "height": 550}, "reveal": {"startMs": 5200, "durationMs": 2000}},
            {"id": "s3_card_day2", "label": "Thẻ Ngày 2", "region": {"x": 550, "y": 750, "width": 490, "height": 250}, "reveal": {"startMs": 7300, "durationMs": 1600}},
            {"id": "s3_bowl_day3_visual", "label": "Hình Bát Ngày 3", "region": {"x": 50, "y": 1300, "width": 500, "height": 550}, "reveal": {"startMs": 9100, "durationMs": 2000}},
            {"id": "s3_card_day3", "label": "Thẻ Ngày 3", "region": {"x": 550, "y": 1350, "width": 490, "height": 250}, "reveal": {"startMs": 11200, "durationMs": 1600}}
        ]
    }
    (OUT_DIR / "scene_03.annotation.json").write_text(json.dumps(ann3, ensure_ascii=False, indent=2), encoding="utf-8")

    # Scene 4 Annotation
    ann4 = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {"id": "s4_mom_baby_visual", "label": "Hình Mẹ Con Hạnh Phúc", "region": {"x": 50, "y": 550, "width": 980, "height": 980}, "reveal": {"startMs": 300, "durationMs": 2800}},
            {"id": "s4_rules_card", "label": "Khung 3 Nguyên Tắc Vàng", "region": {"x": 50, "y": 60, "width": 980, "height": 420}, "reveal": {"startMs": 3200, "durationMs": 2600}},
            {"id": "s4_cta_card", "label": "Thẻ Kêu Gọi Follow Kênh", "region": {"x": 50, "y": 1600, "width": 980, "height": 250}, "reveal": {"startMs": 6000, "durationMs": 2200}}
        ]
    }
    (OUT_DIR / "scene_04.annotation.json").write_text(json.dumps(ann4, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build project.json
    project_json = {
        "schemaVersion": 1,
        "title": "Ăn Dặm Mẹ Dâu - Ngày 01: 3 Ngày Vàng Khởi Động (Voice-First)",
        "version": 1,
        "scenes": [
            {"id": "scene_01", "title": "Cảnh 1: Cảnh báo sốc y khoa quá tải thận", "image": "scene_01.png", "annotation": "scene_01.annotation.json"},
            {"id": "scene_02", "title": "Cảnh 2: So sánh cơ chế dạ dày sữa lỏng và đạm đặc", "image": "scene_02.png", "annotation": "scene_02.annotation.json"},
            {"id": "scene_03", "title": "Cảnh 3: Lộ trình 3 ngày vàng khởi động thực tế", "image": "scene_03.png", "annotation": "scene_03.annotation.json"},
            {"id": "scene_04", "title": "Cảnh 4: 3 Nguyên tắc vàng & Kêu gọi Follow", "image": "scene_04.png", "annotation": "scene_04.annotation.json"}
        ],
        "narration": [
            {
                "id": "cue_01", "sceneId": "scene_01",
                "text": voice_info["cue_01"]["text"],
                "elementIds": ["s1_kidney_visual", "s1_meat_danger_visual", "s1_top_banner", "s1_alert_card"],
                "pauseBeforeMs": 100, "pauseAfterMs": 300
            },
            {
                "id": "cue_02", "sceneId": "scene_02",
                "text": voice_info["cue_02"]["text"],
                "elementIds": ["s2_stomach_milk_visual", "s2_card_milk"],
                "pauseBeforeMs": 100, "pauseAfterMs": 250
            },
            {
                "id": "cue_03", "sceneId": "scene_02",
                "text": voice_info["cue_03"]["text"],
                "elementIds": ["s2_stomach_clogged_visual", "s2_card_clogged"],
                "pauseBeforeMs": 100, "pauseAfterMs": 350
            },
            {
                "id": "cue_04", "sceneId": "scene_03",
                "text": voice_info["cue_04"]["text"],
                "elementIds": ["s3_top_banner"],
                "pauseBeforeMs": 100, "pauseAfterMs": 200
            },
            {
                "id": "cue_05", "sceneId": "scene_03",
                "text": voice_info["cue_05"]["text"],
                "elementIds": ["s3_bowl_day1_visual", "s3_card_day1"],
                "pauseBeforeMs": 100, "pauseAfterMs": 250
            },
            {
                "id": "cue_06", "sceneId": "scene_03",
                "text": voice_info["cue_06"]["text"],
                "elementIds": ["s3_bowl_day2_visual", "s3_card_day2"],
                "pauseBeforeMs": 100, "pauseAfterMs": 250
            },
            {
                "id": "cue_07", "sceneId": "scene_03",
                "text": voice_info["cue_07"]["text"],
                "elementIds": ["s3_bowl_day3_visual", "s3_card_day3"],
                "pauseBeforeMs": 100, "pauseAfterMs": 350
            },
            {
                "id": "cue_08", "sceneId": "scene_04",
                "text": voice_info["cue_08"]["text"],
                "elementIds": ["s4_mom_baby_visual", "s4_rules_card"],
                "pauseBeforeMs": 100, "pauseAfterMs": 250
            },
            {
                "id": "cue_09", "sceneId": "scene_04",
                "text": voice_info["cue_09"]["text"],
                "elementIds": ["s4_cta_card"],
                "pauseBeforeMs": 100, "pauseAfterMs": 400
            }
        ]
    }
    (OUT_DIR / "project.json").write_text(json.dumps(project_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Lưu project.json thành công!")

# ==============================================================================
# BƯỚC 5: RENDER VIDEO VẼ TAY THEO TIMELINE VOICE & GHÉP MP4 HOÀN CHỈNH
# ==============================================================================
def render_video():
    print("\n--- [BƯỚC 4/4] RENDER VIDEO VẼ TAY THEO NHỊP VOICE & GHÉP MP4 ---")
    from whiteboard_app.project import _read_manifest
    from whiteboard_app.timeline import compile_timeline
    from whiteboard_app.renderer import build_commands, subprocess_environment

    manifest_path = OUT_DIR / "project.json"
    project = _read_manifest(manifest_path)
    
    cue_audio_map = {item["cue_id"]: CUES_DIR / f"{item['cue_id']}.wav" for item in SCRIPT_DATA}

    timeline_res = compile_timeline(
        project=project,
        cue_audio=cue_audio_map,
        output_dir=RENDER_DIR,
        on_log=lambda msg: print(f"[Timeline] {msg}")
    )
    project.voice = timeline_res.voice_path
    project.runtime_annotations = timeline_res.runtime_annotations

    commands, _ = build_commands(
        project=project,
        output_dir=RENDER_DIR,
        aspect_ratio="9:16"
    )

    env = subprocess_environment()
    for idx, cmd in enumerate(commands, start=1):
        print(f"\n[{idx}/{len(commands)}] {cmd.label}...")
        proc = subprocess.run(
            cmd.argv, cwd=str(REPO_ROOT), env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if proc.returncode != 0:
            print(f"LỖI TẠI BƯỚC: {cmd.label}")
            print(proc.stderr)
            sys.exit(1)
        else:
            print(f"Hoàn thành: {cmd.label}")

    final_mp4 = RENDER_DIR / "final.mp4"
    if final_mp4.is_file():
        size_mb = final_mp4.stat().st_size / (1024 * 1024)
        print(f"\n🎉 THÀNH CÔNG! VIDEO VOICE-FIRST HOÀN CHỈNH: {final_mp4} ({size_mb:.2f} MB)")
    else:
        print(f"\n⚠️ Chưa thấy file final.mp4 tại {RENDER_DIR}")

if __name__ == "__main__":
    v_info = render_all_voices()
    compose_scenes()
    build_synced_project(v_info)
    render_video()
