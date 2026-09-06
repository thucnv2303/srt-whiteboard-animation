import io
import json
import math
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
from whiteboard_app.voice import generate_scene_voices
from whiteboard_app.timeline import compile_scene_timeline
from whiteboard_app.renderer import build_commands, subprocess_environment

CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")
DRIVE_DIR = Path(r"G:\My Drive\Đăng video")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycby0n2AFHNxWRE2CXlblJuFLm9dJoBzawmonnKkLXDAugrJvZz5WHhbkmWQT6qscAe3VyA/exec"
BRAIN_DIR = Path(r"C:\Users\thucn\.gemini\antigravity\brain\6b62f1b5-8a13-4b72-9245-d5dbac653c8d")

FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segouib.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# Source cartoon images generated via ImageGen
IMG1_SRC = BRAIN_DIR / "s2_rice_confused_baby_1788618103378.jpg"
IMG2_SRC = BRAIN_DIR / "s2_rice_stomach_compare_1788618123852.jpg"
IMG3_SRC = BRAIN_DIR / "s2_rice_three_steps_1788618143697.jpg"
IMG4_SRC = BRAIN_DIR / "s2_rice_mom_feeding_1788618166778.jpg"

OUT_DIR = REPO_ROOT / "projects" / "day_01_slot_02_lively"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = OUT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = OUTPUT_DIR / "audio-scenes"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

THEME_COLOR = (230, 126, 34)       # Warm energetic orange
THEME_DARK = (180, 90, 15)
GREEN_COLOR = (46, 204, 113)       # Soft healthy green
RED_COLOR = (217, 83, 79)          # Coral warning red

def draw_vector_heart(draw, cx, cy, size=20, fill=(231, 76, 60), outline=(255, 255, 255)):
    """Vẽ trái tim vector mượt mà chuẩn hình học, không phụ thuộc font emoji."""
    pts = []
    scale = size / 16.0
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = cx + scale * 16 * (math.sin(rad) ** 3)
        y = cy - scale * (13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad))
        pts.append((x, y))
    draw.polygon(pts, fill=fill, outline=outline)

def draw_ribbon_banner(draw, bbox, fill, outline=(40, 25, 15), text="", font_path=FONT_BOLD, max_font_size=40, text_fill=(255, 255, 255)):
    """Dải ruy băng cuộn tay đuôi én (swallowtail ribbon banner) có auto-fit text & padding an toàn."""
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    w = x1 - x0
    fold_w = 48
    notch = 32
    drop = 20

    tail_fill = (max(0, fill[0] - 50), max(0, fill[1] - 50), max(0, fill[2] - 50))
    # Đuôi trái
    draw.polygon([
        (x0 - fold_w + 10, y0 + drop),
        (x0, y0 + drop),
        (x0, y1 + drop),
        (x0 - fold_w, y1 + drop),
        (x0 - fold_w + notch, y0 + drop + h / 2),
        (x0 - fold_w, y0 + drop)
    ], fill=tail_fill, outline=outline, width=2)

    # Đuôi phải
    draw.polygon([
        (x1 + fold_w - 10, y0 + drop),
        (x1, y0 + drop),
        (x1, y1 + drop),
        (x1 + fold_w, y1 + drop),
        (x1 + fold_w - notch, y0 + drop + h / 2),
        (x1 + fold_w, y0 + drop)
    ], fill=tail_fill, outline=outline, width=2)

    # Tam giác nếp gấp đổ bóng
    draw.polygon([(x0, y1), (x0, y1 + drop), (x0 + 24, y1)], fill=(35, 20, 10), outline=outline)
    draw.polygon([(x1, y1), (x1, y1 + drop), (x1 - 24, y1)], fill=(35, 20, 10), outline=outline)

    # Thân chính ruy băng
    draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=fill, outline=outline, width=3)

    # Nét viền trang trí chỉ khâu
    draw.line([(x0 + 15, y0 + 7), (x1 - 15, y0 + 7)], fill=(255, 255, 255, 120), width=1)
    draw.line([(x0 + 15, y1 - 7), (x1 - 15, y1 - 7)], fill=(255, 255, 255, 120), width=1)

    if text:
        # Khoảng thở an toàn tối thiểu 60px mỗi bên để không chạm mép
        max_text_w = w - 130
        font_size = max_font_size
        font = get_font(font_path, font_size)
        t_bbox = draw.textbbox((0, 0), text, font=font)
        while (t_bbox[2] - t_bbox[0]) > max_text_w and font_size > 22:
            font_size -= 2
            font = get_font(font_path, font_size)
            t_bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((x0 + x1) / 2, (y0 + y1) / 2 - 2), text, font=font, fill=text_fill, anchor="mm")

def draw_speech_bubble(draw, bbox, tail_point, fill=(255, 255, 255, 248), outline=(217, 83, 79), radius=26, width=3):
    """Bóng thoại comic có đuôi chỉ thẳng vào nhân vật."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)
    tx, ty = tail_point
    if ty > y1:
        base_x = (x0 + x1) / 2
        tail_poly = [(base_x - 35, y1 - 2), (base_x + 15, y1 - 2), (tx, ty)]
    else:
        base_x = (x0 + x1) / 2
        tail_poly = [(base_x - 35, y0 + 2), (base_x + 15, y0 + 2), (tx, ty)]
    draw.polygon(tail_poly, fill=fill)
    draw.line([tail_poly[0], (tx, ty), tail_poly[1]], fill=outline, width=width)
    if ty > y1:
        draw.line([(base_x - 33, y1), (base_x + 13, y1)], fill=fill, width=width + 2)
    else:
        draw.line([(base_x - 33, y0), (base_x + 13, y0)], fill=fill, width=width + 2)

def draw_washi_memo_card(draw, bbox, fill=(255, 255, 255, 248), outline=(46, 204, 113), tape_color=(245, 170, 110), width=3):
    """Tờ ghi chú memo có dán băng dính washi tape ở đỉnh."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=20, fill=fill, outline=outline, width=width)
    tape_w = 150
    tape_h = 36
    tx0 = (x0 + x1) / 2 - tape_w / 2
    ty0 = y0 - tape_h / 2
    draw.rectangle((tx0, ty0, tx0 + tape_w, ty0 + tape_h), fill=tape_color, outline=(200, 130, 60), width=1)
    draw.line([(tx0, ty0), (tx0 - 6, ty0 + tape_h / 2), (tx0, ty0 + tape_h)], fill=(200, 130, 60), width=1)
    draw.line([(tx0 + tape_w, ty0), (tx0 + tape_w + 6, ty0 + tape_h / 2), (tx0 + tape_w, ty0 + tape_h)], fill=(200, 130, 60), width=1)

def draw_cta_capsule(draw, bbox, title="BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!", subtext="Đồng hành chăm con khỏe mạnh chuẩn y khoa", fill=THEME_COLOR):
    """Khối CTA bo tròn viên nang có auto-fit text và vị trí icon trái tim cách đều an toàn."""
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    draw.rounded_rectangle(bbox, radius=50, fill=fill, outline=(255, 255, 255), width=3)
    
    max_w = (x1 - x0) - 200
    f_size = 36
    font_head = get_font(FONT_BOLD, f_size)
    t_bbox = draw.textbbox((0, 0), title, font=font_head)
    while (t_bbox[2] - t_bbox[0]) > max_w and f_size > 22:
        f_size -= 2
        font_head = get_font(FONT_BOLD, f_size)
        t_bbox = draw.textbbox((0, 0), title, font=font_head)
    
    tw = t_bbox[2] - t_bbox[0]
    draw.text((cx, y0 + 60), title, font=font_head, fill=(255, 255, 255), anchor="mm")
    
    # Khoảng cách tối thiểu 40px giữa tim và chữ
    left_heart_x = cx - tw / 2 - 40
    right_heart_x = cx + tw / 2 + 40
    draw_vector_heart(draw, left_heart_x, y0 + 60, size=20, fill=(255, 255, 255), outline=None)
    draw_vector_heart(draw, right_heart_x, y0 + 60, size=20, fill=(255, 255, 255), outline=None)
    
    font_sub = get_font(FONT_BOLD, 30)
    draw.text((cx, y0 + 130), subtext, font=font_sub, fill=(255, 255, 255), anchor="mm")

def draw_step_pill_badge(draw, x, y, step_num, title, desc, tag_text=None, theme_color=THEME_COLOR):
    """Thẻ bước kiểu huy hiệu số tròn ❶ ❷ ❸ + thẻ tab + pill badge viên thuốc có auto-fit."""
    circle_r = 44
    cx, cy = x + circle_r, y + circle_r
    draw.ellipse((cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r), fill=theme_color, outline=(255, 255, 255), width=3)
    f_num = get_font(FONT_BOLD, 46)
    draw.text((cx, cy - 2), str(step_num), font=f_num, fill=(255, 255, 255), anchor="mm")

    card_x0 = x + circle_r * 2 + 15
    card_y0 = y
    card_x1 = x + 980
    card_y1 = y + 125
    draw.rounded_rectangle((card_x0, card_y0, card_x1, card_y1), radius=22, fill=(255, 255, 255, 248), outline=theme_color, width=3)

    tag_w = 190
    if tag_text:
        f_tag = get_font(FONT_BOLD, 26)
        tag_h = 42
        tx1 = card_x1 - 18
        tx0 = tx1 - tag_w
        ty0 = card_y0 + 15
        ty1 = ty0 + tag_h
        draw.rounded_rectangle((tx0, ty0, tx1, ty1), radius=21, fill=theme_color, outline=(255, 255, 255), width=2)
        draw.text(((tx0 + tx1) / 2, (ty0 + ty1) / 2 - 1), tag_text, font=f_tag, fill=(255, 255, 255), anchor="mm")

    # Auto-fit title để không đè lên tag viên thuốc
    max_title_w = (card_x1 - 18 - (tag_w if tag_text else 0) - 25) - (card_x0 + 25)
    f_title_size = 35
    f_title = get_font(FONT_BOLD, f_title_size)
    t_bbox = draw.textbbox((0, 0), title, font=f_title)
    while (t_bbox[2] - t_bbox[0]) > max_title_w and f_title_size > 22:
        f_title_size -= 2
        f_title = get_font(FONT_BOLD, f_title_size)
        t_bbox = draw.textbbox((0, 0), title, font=f_title)
    draw.text((card_x0 + 25, card_y0 + 35), title, font=f_title, fill=theme_color, anchor="lm")

    f_desc = get_font(FONT_BOLD, 30)
    draw.text((card_x0 + 25, card_y0 + 85), desc, font=f_desc, fill=(50, 50, 50), anchor="lm")

def compose_scene_1():
    print("  [1/4] Dựng Cảnh 1 (Ribbon Banner + Bong bóng thoại đỏ cảnh báo em bé)...")
    img = Image.open(IMG1_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    draw_ribbon_banner(draw, (110, 65, 970, 185), fill=THEME_COLOR, text="BỮA ĂN DẶM ĐẦU TIÊN CỦA BÉ 6 THÁNG", max_font_size=40)

    draw_speech_bubble(draw, (60, 220, 1020, 465), tail_point=(540, 520), fill=(255, 255, 255, 248), outline=RED_COLOR, radius=26, width=3)
    f_alert_head = get_font(FONT_BOLD, 42)
    f_alert_body = get_font(FONT_BOLD, 35)
    draw.text((540, 280), "TUYỆT ĐỐI KHÔNG TRỘN NẾP & HẠT SEN!", font=f_alert_head, fill=RED_COLOR, anchor="mm")
    draw.text((540, 350), "• Bé 6 tháng chưa có men tiêu hóa tinh bột dẻo", font=f_alert_body, fill=(40, 40, 40), anchor="mm")
    draw.text((540, 415), "• Gây trướng bụng, đầy hơi, nôn trớ & sợ ăn dặm", font=f_alert_body, fill=(185, 28, 28), anchor="mm")

    out_img = OUT_DIR / "scene_01.png"
    img.convert("RGB").save(out_img, quality=95)

    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s1_banner",
                "label": "Ruy Băng Tiêu Đề Cảnh Báo",
                "region": {"x": 40, "y": 50, "width": 1000, "height": 160},
                "reveal": {"startMs": 100, "durationMs": 1800}
            },
            {
                "id": "s1_alert_box",
                "label": "Bong Bóng Thoại Cảnh Báo",
                "region": {"x": 50, "y": 210, "width": 980, "height": 280},
                "reveal": {"startMs": 2000, "durationMs": 3500}
            },
            {
                "id": "s1_baby_visual",
                "label": "Hình Em Bé Hoạt Hình & Bát Hạt",
                "region": {"x": 0, "y": 490, "width": 1080, "height": 1430},
                "reveal": {"startMs": 5600, "durationMs": 7500}
            }
        ]
    }
    (OUT_DIR / "scene_01.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def compose_scene_2():
    print("  [2/4] Dựng Cảnh 2 (Ribbon + Thẻ Washi Tape xanh + Thẻ Cảnh báo đỏ)...")
    img = Image.open(IMG2_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    draw_ribbon_banner(draw, (110, 65, 970, 185), fill=THEME_COLOR, text="TẠI SAO BÉ CHƯA THỂ ĂN GẠO NẾP?", max_font_size=40)

    draw_washi_memo_card(draw, (60, 830, 1020, 980), fill=(255, 255, 255, 248), outline=GREEN_COLOR, tape_color=(120, 220, 160))
    f_label = get_font(FONT_BOLD, 40)
    f_sub = get_font(FONT_BOLD, 33)
    draw.text((540, 875), "CHÁO GẠO TẺ RÂY 1:10 — DỄ TIÊU HÓA", font=f_label, fill=(39, 174, 96), anchor="mm")
    draw.text((540, 935), "Dạ dày 6 tháng bằng quả trứng, hấp thu êm dịu", font=f_sub, fill=(50, 50, 50), anchor="mm")

    draw_washi_memo_card(draw, (60, 1720, 1020, 1880), fill=(255, 255, 255, 248), outline=RED_COLOR, tape_color=(250, 160, 150))
    draw.text((540, 1765), "GẠO NẾP & HẠT SEN — QUÁ TẢI TIÊU HÓA!", font=f_label, fill=RED_COLOR, anchor="mm")
    draw.text((540, 1825), "Thiếu men amylase, gây ứ đọng, trướng bụng & nôn trớ", font=f_sub, fill=(185, 28, 28), anchor="mm")

    out_img = OUT_DIR / "scene_02.png"
    img.convert("RGB").save(out_img, quality=95)

    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s2_banner",
                "label": "Ruy Băng Tiêu Đề Cơ Chế",
                "region": {"x": 40, "y": 50, "width": 1000, "height": 160},
                "reveal": {"startMs": 100, "durationMs": 1800}
            },
            {
                "id": "s2_happy_visual",
                "label": "Hình Dạ Dày Vui Cười",
                "region": {"x": 0, "y": 200, "width": 1080, "height": 610},
                "reveal": {"startMs": 2000, "durationMs": 4000}
            },
            {
                "id": "s2_happy_card",
                "label": "Thẻ Washi Xanh Tiêu Hóa Tốt",
                "region": {"x": 50, "y": 810, "width": 980, "height": 180},
                "reveal": {"startMs": 6100, "durationMs": 2800}
            },
            {
                "id": "s2_stressed_visual",
                "label": "Hình Dạ Dày Quá Tải",
                "region": {"x": 0, "y": 990, "width": 1080, "height": 720},
                "reveal": {"startMs": 9000, "durationMs": 4500}
            },
            {
                "id": "s2_stressed_card",
                "label": "Thẻ Washi Đỏ Quá Tải",
                "region": {"x": 50, "y": 1700, "width": 980, "height": 190},
                "reveal": {"startMs": 13600, "durationMs": 3000}
            }
        ]
    }
    (OUT_DIR / "scene_02.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def compose_scene_3():
    print("  [3/4] Dựng Cảnh 3 (Ribbon + 3 Huy hiệu số tròn ❶ ❷ ❸ + Pill Tag)...")
    img = Image.open(IMG3_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    draw_ribbon_banner(draw, (110, 65, 970, 185), fill=THEME_COLOR, text="CÔNG THỨC CHÁO RÂY 1:10 CHUẨN Y KHOA", max_font_size=40)

    draw_step_pill_badge(draw, 50, 535, "1", "BƯỚC 1: GẠO TẺ NGUYÊN CÁM", "Chọn gạo thơm mới, vo nhẹ 1 lần giữ vitamin B1", tag_text="VITAMIN B1", theme_color=THEME_COLOR)
    draw_step_pill_badge(draw, 50, 1135, "2", "BƯỚC 2: TỶ LỆ VÀNG 1 : 10", "Đong 10g gạo với 100ml nước, ninh nhỏ lửa 45 phút", tag_text="NINH 45 PHÚT", theme_color=THEME_COLOR)
    draw_step_pill_badge(draw, 50, 1725, "3", "BƯỚC 3: RÂY MỊN KHI ẤM NÓNG", "Rây qua lưới 0.5mm, miết lưng thìa lấy cháo sánh", tag_text="LƯỚI 0.5MM", theme_color=THEME_COLOR)

    out_img = OUT_DIR / "scene_03.png"
    img.convert("RGB").save(out_img, quality=95)

    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s3_banner",
                "label": "Ruy Băng Tiêu Đề Công Thức",
                "region": {"x": 40, "y": 50, "width": 1000, "height": 160},
                "reveal": {"startMs": 150, "durationMs": 3800}
            },
            {
                "id": "s3_step1_visual",
                "label": "Hình Vẽ Bao Gạo",
                "region": {"x": 0, "y": 190, "width": 1080, "height": 330},
                "reveal": {"startMs": 4000, "durationMs": 4000}
            },
            {
                "id": "s3_step1_card",
                "label": "Huy Hiệu Bước 1 Gạo Tẻ",
                "region": {"x": 40, "y": 520, "width": 1000, "height": 150},
                "reveal": {"startMs": 8100, "durationMs": 4000}
            },
            {
                "id": "s3_step2_visual",
                "label": "Hình Vẽ Nồi Cháo",
                "region": {"x": 0, "y": 670, "width": 1080, "height": 450},
                "reveal": {"startMs": 12200, "durationMs": 4000}
            },
            {
                "id": "s3_step2_card",
                "label": "Huy Hiệu Bước 2 Tỷ Lệ 1:10",
                "region": {"x": 40, "y": 1120, "width": 1000, "height": 150},
                "reveal": {"startMs": 16300, "durationMs": 4000}
            },
            {
                "id": "s3_step3_visual",
                "label": "Hình Vẽ Lưới Rây",
                "region": {"x": 0, "y": 1270, "width": 1080, "height": 440},
                "reveal": {"startMs": 20400, "durationMs": 4000}
            },
            {
                "id": "s3_step3_card",
                "label": "Huy Hiệu Bước 3 Rây Mịn",
                "region": {"x": 40, "y": 1710, "width": 1000, "height": 160},
                "reveal": {"startMs": 24500, "durationMs": 4000}
            }
        ]
    }
    (OUT_DIR / "scene_03.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def compose_scene_4():
    print("  [4/4] Dựng Cảnh 4 (Ribbon + Thẻ Memo dán Washi + Heart CTA Pill)...")
    img = Image.open(IMG4_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)

    draw_ribbon_banner(draw, (110, 65, 970, 185), fill=THEME_COLOR, text="NGUYÊN TẮC VÀNG BỮA ĐẦU TIÊN", max_font_size=40)

    draw_washi_memo_card(draw, (60, 1300, 1020, 1600), fill=(255, 255, 255, 248), outline=THEME_COLOR, tape_color=(245, 170, 110))
    f_check_head = get_font(FONT_BOLD, 40)
    f_check_body = get_font(FONT_BOLD, 33)
    draw.text((540, 1350), "CHỈ NẾM 1 - 2 THÌA CÀ PHÊ NHỎ (5ML)", font=f_check_head, fill=THEME_COLOR, anchor="mm")
    draw.text((540, 1410), "• Ăn cữ sáng 9h - 10h khi con tỉnh táo, vui vẻ", font=f_check_body, fill=(40, 40, 40), anchor="mm")
    draw.text((540, 1465), "• Tuyệt đối KHÔNG nêm mắm, muối, gia vị hay dầu ăn", font=f_check_body, fill=(220, 38, 38), anchor="mm")
    draw.text((540, 1520), "• Theo dõi phân và da của con trong 3 ngày liên tiếp", font=f_check_body, fill=(40, 40, 40), anchor="mm")

    cta_bbox = (60, 1670, 1020, 1870)
    draw_cta_capsule(draw, cta_bbox, title="BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!", subtext="Đồng hành chăm con khỏe mạnh chuẩn y khoa", fill=THEME_COLOR)

    out_img = OUT_DIR / "scene_04.png"
    img.convert("RGB").save(out_img, quality=95)

    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s4_banner",
                "label": "Ruy Băng Tiêu Đề Nguyên Tắc",
                "region": {"x": 40, "y": 50, "width": 1000, "height": 160},
                "reveal": {"startMs": 100, "durationMs": 1800}
            },
            {
                "id": "s4_mom_feeding",
                "label": "Hình Vẽ Mẹ Đút Bé",
                "region": {"x": 0, "y": 190, "width": 1080, "height": 1090},
                "reveal": {"startMs": 2000, "durationMs": 5500}
            },
            {
                "id": "s4_advice_checklist",
                "label": "Thẻ Memo Ghi Nhớ Lời Khuyên",
                "region": {"x": 50, "y": 1280, "width": 980, "height": 340},
                "reveal": {"startMs": 7600, "durationMs": 3500}
            },
            {
                "id": "s4_follow_cta",
                "label": "Huy Hiệu Trái Tim Follow Mẹ Dâu",
                "region": {"x": 50, "y": 1650, "width": 980, "height": 240},
                "reveal": {"startMs": 11200, "durationMs": 2800}
            }
        ]
    }
    (OUT_DIR / "scene_04.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def main():
    print("=== SẢN XUẤT SLOT 2 NÂNG CẤP HÌNH DẠNG ĐA DẠNG NGHỆ THUẬT (2K 1440x2560) ===")

    # 1. Compose all 4 scenes with new shapes
    compose_scene_1()
    compose_scene_2()
    compose_scene_3()
    compose_scene_4()

    # 2. Tạo manifest project.json
    project_manifest = {
        "schemaVersion": 1,
        "title": "Gạo Tẻ Nấu Cháo Rây Bé Mấy Tháng Ăn Được?",
        "aspectRatio": "9:16 2K",
        "penBrand": "Ăn dặm mẹ Dâu",
        "scenes": [
            {"id": "scene_01", "title": "Cảnh báo nhầm lẫn", "image": "scene_01.png", "annotation": "scene_01.annotation.json"},
            {"id": "scene_02", "title": "Giải mã tiêu hóa", "image": "scene_02.png", "annotation": "scene_02.annotation.json"},
            {"id": "scene_03", "title": "Công thức 3 bước", "image": "scene_03.png", "annotation": "scene_03.annotation.json"},
            {"id": "scene_04", "title": "Lời khuyên & CTA", "image": "scene_04.png", "annotation": "scene_04.annotation.json"}
        ],
        "narration": [
            {
                "id": "cue_01",
                "sceneId": "scene_01",
                "text": "Rất nhiều mẹ hỏi Mẹ Dâu: Bé tròn sáu tháng bắt đầu ăn dặm, có nên trộn thêm gạo nếp, hạt sen hay đậu xanh vào nấu cháo cho con nhanh tăng cân không? Câu trả lời dứt khoát là tuyệt đối không mẹ nhé! Đây là sai lầm kinh điển khiến hệ tiêu hóa non nớt của con bị quá tải ngay từ bữa đầu tiên.",
                "elementIds": ["s1_banner", "s1_alert_box", "s1_baby_visual"],
                "pauseBeforeMs": 100
            },
            {
                "id": "cue_02",
                "sceneId": "scene_02",
                "text": "Mẹ biết không, dạ dày bé sáu tháng chỉ nhỏ bằng một quả trứng gà. Tuyến tụy của con mới chỉ tiết một lượng rất ít men amylase để phân giải tinh bột thuần từ gạo tẻ. Tinh bột amylopectin trong gạo nếp lại cực kỳ khó cắt đứt liên kết, còn hạt sen lại chứa hàm lượng chất đạm thực vật phức tạp. Trộn vào lúc này sẽ khiến đường ruột con bị lên men ứ đọng, gây chướng bụng, quấy khóc cả đêm và nôn trớ sợ ăn.",
                "elementIds": ["s2_banner", "s2_happy_visual", "s2_happy_card", "s2_stressed_visual", "s2_stressed_card"],
                "pauseBeforeMs": 100
            },
            {
                "id": "cue_03",
                "sceneId": "scene_03",
                "text": "Để con có bữa ăn đầu đời hoàn hảo, mẹ làm đúng ba bước sau: Bước một: Chọn gạo tẻ thơm nguyên cám giàu vitamin nhóm B, chỉ vo nhẹ tay một lần với nước sạch để giữ trọn dưỡng chất. Bước hai: Đong chuẩn mười gam gạo với một trăm mililít nước theo đúng tỷ lệ vàng một mười kiểu Nhật. Ninh lửa nhỏ liu riu trong bốn mươi lăm phút cho hạt gạo nở bung mềm nhừ. Bước ba: Khi cháo còn ấm nóng, mẹ đổ qua rây mắt nhỏ không phẩy năm milimét, dùng lưng thìa miết nhẹ hai lần. Phần cháo thu được sẽ sánh mịn đồng nhất như sữa mẹ, giúp con nuốt êm ái mà không sợ nghẹn hóc.",
                "elementIds": ["s3_banner", "s3_step1_visual", "s3_step1_card", "s3_step2_visual", "s3_step2_card", "s3_step3_visual", "s3_step3_card"],
                "pauseBeforeMs": 100
            },
            {
                "id": "cue_04",
                "sceneId": "scene_04",
                "text": "Bữa đầu tiên, mẹ chỉ cho con nếm thử một đến hai thìa cà phê nhỏ vào cữ sáng khi con tỉnh táo. Tuyệt đối không nêm bất kỳ giọt mắm, muối hay dầu ăn nào vì thận của con chưa lọc được mẹ nhé. Sau ăn, mẹ quan sát phân và da con trong ba ngày liên tiếp. Mẹ hãy bấm lưu video và Follow Ăn dặm mẹ Dâu để cùng mẹ đồng hành chăm con chuẩn y khoa nhé!",
                "elementIds": ["s4_banner", "s4_mom_feeding", "s4_advice_checklist", "s4_follow_cta"],
                "pauseBeforeMs": 100
            }
        ]
    }
    manifest_path = OUT_DIR / "project.json"
    manifest_path.write_text(json.dumps(project_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    project = _read_manifest(manifest_path)

    # 3. Tạo giọng đọc Xuân Dung (OmniVoice Clean)
    print("\n--- BƯỚC 2: TẠO GIỌNG ĐỌC XUÂN DUNG LIỀN MẠCH 4 CẢNH (OMNIVOICE CLEAN) ---")
    scene_audio_map = generate_scene_voices(
        cli_path=CLI_PATH,
        project=project,
        reference_audio=VOICE_REF,
        output_dir=AUDIO_DIR,
        on_log=lambda msg: print(f"  [OmniVoice] {msg}"),
        cancel_event=threading.Event(),
        reference_text="Muốn đổi món với thịt bò cho bé, đây là 5 gợi ý dễ ăn.",
    )

    # 4. Biên dịch Timeline & Đồng bộ Whiteboard với 1.0s (1000ms) gaze time
    print("\n--- BƯỚC 3: BIÊN DỊCH TIMELINE & ĐỒNG BỘ NÉT VẼ TAY (GAZE 1000MS) ---")
    timeline_res = compile_scene_timeline(
        project=project,
        scene_audio=scene_audio_map,
        output_dir=OUTPUT_DIR,
        on_log=lambda m: None,
        gaze_ms=1000
    )
    project.voice = timeline_res.voice_path
    project.runtime_annotations = timeline_res.runtime_annotations
    duration_s = timeline_res.total_duration_ms / 1000
    print(f"  Thời lượng video chuẩn: {duration_s:.1f}s")

    # 5. Render video vẽ tay 2K (1440x2560)
    print("\n--- BƯỚC 4: RENDER VIDEO VẼ TAY GPU 2K (1440x2560) ---")
    commands, final_target = build_commands(
        project=project,
        output_dir=OUTPUT_DIR,
        aspect_ratio="9:16 2K"
    )

    env = subprocess_environment()
    for cmd_idx, cmd in enumerate(commands, start=1):
        print(f"  [{cmd_idx}/{len(commands)}] {cmd.label}...")
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
            sys.exit(1)

    final_mp4 = OUTPUT_DIR / "final.mp4"
    if not final_mp4.is_file():
        raise RuntimeError(f"Chưa thấy file final.mp4 tại {OUTPUT_DIR}")

    # 6. Export to Google Drive
    drive_dest = DRIVE_DIR / "Day_01_Slot_02_Gạo_Tẻ_Nấu_Cháo_Rây_Bé_Mấy_Tháng_Ăn_Được_2K.mp4"
    shutil.copy2(final_mp4, drive_dest)
    print(f"\n🎉 ĐÃ XUẤT BẢN THÀNH CÔNG SANG GOOGLE DRIVE:")
    print(f"  File: {drive_dest} ({drive_dest.stat().st_size / (1024*1024):.2f} MB, {duration_s:.1f}s)")

    # 7. Update Google Sheets Webhook
    payload = {
        "action": "update_row",
        "day": 1,
        "slot_id": 2,
        "video_path": str(drive_dest),
        "status": f"READY_TO_PUBLISH (2K 1440x2560 - {duration_s:.1f}s)"
    }
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"  Google Sheets Update: {resp.read().decode('utf-8')}")

if __name__ == "__main__":
    main()
