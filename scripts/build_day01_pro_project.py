import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Set up paths
REPO_ROOT = Path(r"E:\Project AI\Tạo video vẽ tay")
BRAIN_DIR = Path(r"C:\Users\thucn\.gemini\antigravity\brain\6b62f1b5-8a13-4b72-9245-d5dbac653c8d")
OUT_DIR = REPO_ROOT / "output" / "day_01_pro"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Image sources
IMG1_SRC = BRAIN_DIR / "scene1_baby_warning_1788494364040.jpg"
IMG2_SRC = BRAIN_DIR / "scene2_three_bowls_1788494382133.jpg"
IMG3_SRC = BRAIN_DIR / "scene3_mom_feeding_1788494416555.jpg"

# Fonts
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segouib.ttf"
FONT_SEGOE = r"C:\Windows\Fonts\segoeui.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def compose_scene_1():
    print("Composing Scene 1...")
    img = Image.open(IMG1_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Header Banner
    draw_rounded_rect(draw, (60, 80, 1020, 200), radius=24, fill=(220, 38, 38, 240), outline=(255, 255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 52)
    draw.text((540, 140), "CẢNH BÁO ĂN DẶM CHO BÉ", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Subtitle Tag
    draw_rounded_rect(draw, (340, 220, 740, 285), radius=16, fill=(245, 158, 11, 245))
    f_sub = get_font(FONT_SEGOE_BOLD, 34)
    draw.text((540, 252), "BÉ 6 THÁNG TUỔI", font=f_sub, fill=(255, 255, 255), anchor="mm")
    
    # 3. Warning Card 1: Mistake
    draw_rounded_rect(draw, (60, 310, 1020, 480), radius=20, fill=(255, 255, 255, 235), outline=(239, 68, 68), width=3)
    f_card_title = get_font(FONT_BOLD, 40)
    f_card_body = get_font(FONT_SEGOE_BOLD, 34)
    draw.text((100, 360), "SAI LẦM PHỔ BIẾN:", font=f_card_title, fill=(220, 38, 38), anchor="lm")
    draw.text((100, 425), "Chớ vội nấu cháo thịt bò, chim bồ câu tẩm bổ!", font=f_card_body, fill=(31, 41, 55), anchor="lm")
    
    # 4. Reason Card (Bottom overlay)
    draw_rounded_rect(draw, (60, 1450, 1020, 1820), radius=24, fill=(255, 255, 255, 245), outline=(245, 158, 11), width=3)
    f_reason_head = get_font(FONT_BOLD, 42)
    f_reason_body = get_font(FONT_SEGOE, 34)
    f_reason_bold = get_font(FONT_SEGOE_BOLD, 34)
    
    draw.text((100, 1510), "TẠI SAO PHẢI DỪNG LẠI?", font=f_reason_head, fill=(217, 119, 6), anchor="lm")
    draw.text((100, 1580), "• Thận bé 6 tháng còn rất non nớt, chưa lọc được đạm đặc.", font=f_reason_body, fill=(55, 65, 81), anchor="lm")
    draw.text((100, 1650), "• Ăn đạm sớm gây quá tải thận, nôn trớ và táo bón.", font=f_reason_body, fill=(55, 65, 81), anchor="lm")
    draw.text((100, 1730), "• Dễ khiến con sợ ăn dặm kéo dài!", font=f_reason_bold, fill=(220, 38, 38), anchor="lm")
    
    out_img = OUT_DIR / "scene_01.png"
    img.convert("RGB").save(out_img, quality=95)
    
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s1_banner",
                "label": "Banner Cảnh Báo",
                "region": {"x": 60, "y": 80, "width": 960, "height": 205},
                "reveal": {"startMs": 500, "durationMs": 1200}
            },
            {
                "id": "s1_mistake_card",
                "label": "Thẻ Sai Lầm",
                "region": {"x": 60, "y": 310, "width": 960, "height": 170},
                "reveal": {"startMs": 2000, "durationMs": 1500}
            },
            {
                "id": "s1_baby_visual",
                "label": "Hình Ảnh Bé",
                "region": {"x": 100, "y": 500, "width": 880, "height": 900},
                "reveal": {"startMs": 3800, "durationMs": 1800}
            },
            {
                "id": "s1_reason_card",
                "label": "Thẻ Giải Thích Khoa Học",
                "region": {"x": 60, "y": 1450, "width": 960, "height": 370},
                "reveal": {"startMs": 6000, "durationMs": 2500}
            }
        ]
    }
    (OUT_DIR / "scene_01.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def compose_scene_2():
    print("Composing Scene 2...")
    img = Image.open(IMG2_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Header Banner
    draw_rounded_rect(draw, (60, 80, 1020, 200), radius=24, fill=(16, 185, 129, 240), outline=(255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 50)
    draw.text((540, 140), "3 NGÀY VÀNG KHỞI ĐỘNG", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Card Day 1 (Blue)
    draw_rounded_rect(draw, (60, 230, 1020, 420), radius=20, fill=(255, 255, 255, 240), outline=(59, 130, 246), width=3)
    draw_rounded_rect(draw, (80, 250, 300, 310), radius=12, fill=(59, 130, 246))
    f_badge = get_font(FONT_BOLD, 32)
    f_c_title = get_font(FONT_BOLD, 38)
    f_c_desc = get_font(FONT_SEGOE, 32)
    draw.text((190, 280), "NGÀY 1", font=f_badge, fill=(255, 255, 255), anchor="mm")
    draw.text((320, 280), "Cháo rây 1:10 thật loãng mịn", font=f_c_title, fill=(30, 64, 175), anchor="lm")
    draw.text((100, 365), "• Khởi động 1-2 thìa nhỏ để làm quen phản xạ nuốt thức ăn.", font=f_c_desc, fill=(55, 65, 81), anchor="lm")
    
    # 3. Card Day 2 (Green)
    draw_rounded_rect(draw, (60, 440, 1020, 630), radius=20, fill=(255, 255, 255, 240), outline=(16, 185, 129), width=3)
    draw_rounded_rect(draw, (80, 460, 300, 520), radius=12, fill=(16, 185, 129))
    draw.text((190, 490), "NGÀY 2", font=f_badge, fill=(255, 255, 255), anchor="mm")
    draw.text((320, 490), "Cháo trộn sữa mẹ thơm ngon", font=f_c_title, fill=(4, 120, 87), anchor="lm")
    draw.text((100, 575), "• Mùi vị quen thuộc giúp con hào hứng và hợp tác vui vẻ.", font=f_c_desc, fill=(55, 65, 81), anchor="lm")
    
    # 4. Card Day 3 (Orange)
    draw_rounded_rect(draw, (60, 650, 1020, 840), radius=20, fill=(255, 255, 255, 240), outline=(249, 115, 22), width=3)
    draw_rounded_rect(draw, (80, 670, 300, 730), radius=12, fill=(249, 115, 22))
    draw.text((190, 700), "NGÀY 3", font=f_badge, fill=(255, 255, 255), anchor="mm")
    draw.text((320, 700), "Thêm 1 thìa bí đỏ rây nhuyễn", font=f_c_title, fill=(194, 65, 12), anchor="lm")
    draw.text((100, 785), "• Bổ sung Vitamin A và chất xơ tự nhiên, vị ngọt dịu dễ ăn.", font=f_c_desc, fill=(55, 65, 81), anchor="lm")
    
    out_img = OUT_DIR / "scene_02.png"
    img.convert("RGB").save(out_img, quality=95)
    
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s2_banner",
                "label": "Banner 3 Ngày Vàng",
                "region": {"x": 60, "y": 80, "width": 960, "height": 120},
                "reveal": {"startMs": 400, "durationMs": 1000}
            },
            {
                "id": "s2_day1_card",
                "label": "Thẻ Ngày 1 Cháo Rây",
                "region": {"x": 60, "y": 230, "width": 960, "height": 190},
                "reveal": {"startMs": 1600, "durationMs": 1800}
            },
            {
                "id": "s2_day2_card",
                "label": "Thẻ Ngày 2 Cháo Sữa",
                "region": {"x": 60, "y": 440, "width": 960, "height": 190},
                "reveal": {"startMs": 3700, "durationMs": 1800}
            },
            {
                "id": "s2_day3_card",
                "label": "Thẻ Ngày 3 Bí Đỏ",
                "region": {"x": 60, "y": 650, "width": 960, "height": 190},
                "reveal": {"startMs": 5800, "durationMs": 1800}
            },
            {
                "id": "s2_bowls_visual",
                "label": "Hình 3 Bát Ăn Dặm Thực Tế",
                "region": {"x": 100, "y": 870, "width": 880, "height": 1000},
                "reveal": {"startMs": 7800, "durationMs": 2200}
            }
        ]
    }
    (OUT_DIR / "scene_02.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def compose_scene_3():
    print("Composing Scene 3...")
    img = Image.open(IMG3_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Header Banner
    draw_rounded_rect(draw, (60, 80, 1020, 200), radius=24, fill=(147, 51, 234, 240), outline=(255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 48)
    draw.text((540, 140), "3 NGUYÊN TẮC VÀNG TỪ CHUYÊN GIA", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Principles Card (Top)
    draw_rounded_rect(draw, (60, 230, 1020, 560), radius=20, fill=(255, 255, 255, 245), outline=(147, 51, 234), width=3)
    f_p_head = get_font(FONT_BOLD, 36)
    f_p_body = get_font(FONT_SEGOE_BOLD, 34)
    
    draw.text((100, 280), "GHI NHỚ QUAN TRỌNG:", font=f_p_head, fill=(126, 34, 206), anchor="lm")
    draw.text((100, 350), "1. Ăn từ ít đến nhiều (1-2 thìa ➡️ nửa bát)", font=f_p_body, fill=(31, 41, 55), anchor="lm")
    draw.text((100, 420), "2. Ăn từ loãng đến đặc (tập phản xạ nhai nuốt)", font=f_p_body, fill=(31, 41, 55), anchor="lm")
    draw.text((100, 490), "3. Tuyệt đối KHÔNG nêm mắm, muối, đường", font=f_p_body, fill=(220, 38, 38), anchor="lm")
    
    # 3. Bottom CTA Card
    draw_rounded_rect(draw, (60, 1530, 1020, 1820), radius=24, fill=(236, 72, 153, 245), outline=(255, 255, 255), width=4)
    f_cta_1 = get_font(FONT_BOLD, 44)
    f_cta_2 = get_font(FONT_SEGOE_BOLD, 36)
    f_cta_3 = get_font(FONT_BOLD, 48)
    
    draw.text((540, 1600), "ĂN DẶM MẸ DÂU", font=f_cta_3, fill=(255, 255, 255), anchor="mm")
    draw.text((540, 1675), "Đồng hành nuôi con khoa học & nhàn tênh", font=f_cta_2, fill=(255, 241, 242), anchor="mm")
    draw.text((540, 1750), "❤️ Bấm Follow kênh để xem video Ngày 2 nhé!", font=f_cta_1, fill=(255, 255, 255), anchor="mm")
    
    out_img = OUT_DIR / "scene_03.png"
    img.convert("RGB").save(out_img, quality=95)
    
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s3_banner",
                "label": "Banner Nguyên Tắc Vàng",
                "region": {"x": 60, "y": 80, "width": 960, "height": 120},
                "reveal": {"startMs": 400, "durationMs": 1000}
            },
            {
                "id": "s3_rules_card",
                "label": "Thẻ 3 Quy Tắc Bắt Buộc",
                "region": {"x": 60, "y": 230, "width": 960, "height": 330},
                "reveal": {"startMs": 1600, "durationMs": 2200}
            },
            {
                "id": "s3_mother_visual",
                "label": "Hình Mẹ Cho Bé Ăn Vui Vẻ",
                "region": {"x": 100, "y": 600, "width": 880, "height": 900},
                "reveal": {"startMs": 4000, "durationMs": 2200}
            },
            {
                "id": "s3_cta_card",
                "label": "Thẻ Kêu Gọi Follow Kênh",
                "region": {"x": 60, "y": 1530, "width": 960, "height": 290},
                "reveal": {"startMs": 6400, "durationMs": 2000}
            }
        ]
    }
    (OUT_DIR / "scene_03.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

def build_project_json():
    project_data = {
        "schemaVersion": 1,
        "title": "Ăn Dặm Mẹ Dâu - Ngày 01: 3 Ngày Vàng Khởi Động",
        "version": 1,
        "scenes": [
            {
                "id": "scene_01",
                "title": "Cảnh 1: Cảnh báo sai lầm cho bé ăn thịt sớm",
                "image": "scene_01.png",
                "annotation": "scene_01.annotation.json"
            },
            {
                "id": "scene_02",
                "title": "Cảnh 2: Lộ trình 3 ngày vàng khởi động",
                "image": "scene_02.png",
                "annotation": "scene_02.annotation.json"
            },
            {
                "id": "scene_03",
                "title": "Cảnh 3: Nguyên tắc vàng và CTA Follow",
                "image": "scene_03.png",
                "annotation": "scene_03.annotation.json"
            }
        ],
        "narration": [
            {
                "id": "cue_01",
                "sceneId": "scene_01",
                "text": "Dừng lại ngay! Bé sáu tháng mới tập ăn dặm, mẹ chớ vội nấu cháo thịt bò hay chim bồ câu tẩm bổ!",
                "elementIds": ["s1_banner", "s1_mistake_card", "s1_baby_visual"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_02",
                "sceneId": "scene_01",
                "text": "Tại sao ư? Vì thận của con lúc này còn rất non nớt, chưa thể lọc được lượng đạm đặc. Cho ăn sớm sẽ khiến con quá tải thận, táo bón và sợ ăn dặm cả đời!",
                "elementIds": ["s1_reason_card"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 400
            },
            {
                "id": "cue_03",
                "sceneId": "scene_02",
                "text": "Thay vào đó, mẹ hãy bắt đầu chuẩn chỉnh với ba ngày vàng khoa học này nhé!",
                "elementIds": ["s2_banner"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_04",
                "sceneId": "scene_02",
                "text": "Ngày một: Cho bé thử một đến hai thìa cháo rây tỉ lệ một mười, nấu thật loãng và mịn như sữa mẹ.",
                "elementIds": ["s2_day1_card"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_05",
                "sceneId": "scene_02",
                "text": "Ngày hai: Trộn thêm chút sữa mẹ vào cháo để tạo hương vị quen thuộc giúp con hào hứng hợp tác.",
                "elementIds": ["s2_day2_card"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_06",
                "sceneId": "scene_02",
                "text": "Ngày ba: Thêm một thìa nhỏ bí đỏ rây nhuyễn để bổ sung vitamin A và chất xơ tự nhiên!",
                "elementIds": ["s2_day3_card", "s2_bowls_visual"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 400
            },
            {
                "id": "cue_07",
                "sceneId": "scene_03",
                "text": "Mẹ ghi nhớ ba nguyên tắc: Ăn từ ít đến nhiều, từ loãng đến đặc và tuyệt đối không nêm mắm muối gia vị dưới một tuổi nhé!",
                "elementIds": ["s3_banner", "s3_rules_card", "s3_mother_visual"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_08",
                "sceneId": "scene_03",
                "text": "Lưu lại ngay video này và bấm Follow kênh Ăn dặm mẹ Dâu để nhận trọn bộ thực đơn khoa học mỗi ngày nhé!",
                "elementIds": ["s3_cta_card"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 500
            }
        ]
    }
    (OUT_DIR / "project.json").write_text(json.dumps(project_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved project.json")

if __name__ == "__main__":
    compose_scene_1()
    compose_scene_2()
    compose_scene_3()
    build_project_json()
    print("Project build ready in:", OUT_DIR)
