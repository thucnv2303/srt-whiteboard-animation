import io
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

REPO_ROOT = Path(r"E:\Project AI\Tạo video vẽ tay")
BRAIN_DIR = Path(r"C:\Users\thucn\.gemini\antigravity\brain\6b62f1b5-8a13-4b72-9245-d5dbac653c8d")
OUT_DIR = REPO_ROOT / "output" / "day_01_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Image sources
IMG1_SRC = BRAIN_DIR / "s1_kidney_warning_v2_1788505424553.jpg"
IMG2_SRC = BRAIN_DIR / "s2_stomach_compare_v2_1788505444073.jpg"
IMG3_SRC = BRAIN_DIR / "s3_golden_steps_v2_1788505463380.jpg"
IMG4_SRC = BRAIN_DIR / "s4_happy_feeding_v2_1788505528006.jpg"

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

# ==============================================================================
# SCENE 1: CẢNH BÁO SỐC Y KHOA (THẬN NON NỚT & BÁT CHÁO THỊT)
# ==============================================================================
def compose_scene_1():
    print("Composing Scene 1 (Cảnh báo quá tải thận)...")
    img = Image.open(IMG1_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Warning Banner
    draw_rounded_rect(draw, (60, 60, 1020, 180), radius=24, fill=(220, 38, 38, 245), outline=(255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 46)
    draw.text((540, 120), "🚨 CẢNH BÁO NGUY HIỂM CHO BÉ 6 THÁNG", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Bottom Critical Alert Box
    draw_rounded_rect(draw, (60, 1420, 1020, 1840), radius=24, fill=(255, 255, 255, 245), outline=(220, 38, 38), width=3)
    f_alert_head = get_font(FONT_BOLD, 40)
    f_alert_body = get_font(FONT_SEGOE_BOLD, 33)
    f_alert_danger = get_font(FONT_BOLD, 35)
    
    draw.text((100, 1480), "CHỚ VỘI CHO ĂN ĐẠM ĐẶC QUÁ SỚM!", font=f_alert_head, fill=(220, 38, 38), anchor="lm")
    draw.text((100, 1555), "• Thận bé 6 tháng còn rất non nớt, chưa thể lọc đạm.", font=f_alert_body, fill=(31, 41, 55), anchor="lm")
    draw.text((100, 1630), "• Cháo thịt bò, chim bồ câu gây QUÁ TẢI & TỔN THƯƠNG THẬN!", font=f_alert_danger, fill=(185, 28, 28), anchor="lm")
    draw.text((100, 1710), "• Con dễ bị đầy bụng, táo bón nặng & nôn trớ sợ ăn!", font=f_alert_body, fill=(31, 41, 55), anchor="lm")
    draw.text((100, 1785), "⚠️ DỪNG LẠI NGAY ĐỂ BẢO VỆ CON!", font=f_alert_head, fill=(217, 119, 6), anchor="lm")
    
    out_img = OUT_DIR / "scene_01.png"
    img.convert("RGB").save(out_img, quality=95)
    
    # Thứ tự: Hình ảnh thận & bát cháo thịt trước (1, 2) -> Sau đó mới vẽ Chữ (3, 4)
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s1_kidney_visual",
                "label": "Hình Ảnh Quả Thận Cảnh Báo",
                "region": {"x": 40, "y": 200, "width": 550, "height": 1180},
                "reveal": {"startMs": 400, "durationMs": 2800}
            },
            {
                "id": "s1_meat_danger_visual",
                "label": "Hình Bát Cháo Thịt Bị Gạch Đỏ",
                "region": {"x": 580, "y": 380, "width": 460, "height": 980},
                "reveal": {"startMs": 3300, "durationMs": 2500}
            },
            {
                "id": "s1_top_banner",
                "label": "Banner Cảnh Báo Đầu Đề",
                "region": {"x": 60, "y": 60, "width": 960, "height": 120},
                "reveal": {"startMs": 6000, "durationMs": 1400}
            },
            {
                "id": "s1_bottom_alert_card",
                "label": "Thẻ Cảnh Báo Y Khoa",
                "region": {"x": 60, "y": 1420, "width": 960, "height": 420},
                "reveal": {"startMs": 7600, "durationMs": 2600}
            }
        ]
    }
    (OUT_DIR / "scene_01.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

# ==============================================================================
# SCENE 2: SO SÁNH DẠ DÀY NON NỚT (HÌNH ẢNH TRƯỚC -> CHỮ SAU)
# ==============================================================================
def compose_scene_2():
    print("Composing Scene 2 (So sánh dạ dày non nớt)...")
    img = Image.open(IMG2_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Header Banner
    draw_rounded_rect(draw, (60, 50, 1020, 155), radius=20, fill=(37, 99, 235, 245), outline=(255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 44)
    draw.text((540, 102), "TẠI SAO BÉ CHƯA THỂ ĂN ĐẶC?", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Tag Panel 1: Sữa lỏng (Top Right)
    draw_rounded_rect(draw, (60, 780, 1020, 930), radius=16, fill=(255, 255, 255, 245), outline=(16, 185, 129), width=3)
    f_tag_title = get_font(FONT_BOLD, 36)
    f_tag_sub = get_font(FONT_SEGOE_BOLD, 30)
    draw.text((100, 825), "✅ DẠ DÀY 6 THÁNG: CHỈ QUEN SỮA LỎNG", font=f_tag_title, fill=(5, 150, 105), anchor="lm")
    draw.text((100, 885), "• Tiêu hóa êm ái, trơn tru, không gây áp lực đường ruột.", font=f_tag_sub, fill=(55, 65, 81), anchor="lm")
    
    # 3. Tag Panel 2: Đạm đặc (Bottom Card)
    draw_rounded_rect(draw, (60, 1680, 1020, 1860), radius=20, fill=(255, 255, 255, 245), outline=(220, 38, 38), width=3)
    draw.text((100, 1730), "❌ ĂN ĐẶM ĐẶC SỚM: TÁO BÓN & NÔN TRỚ!", font=f_tag_title, fill=(220, 38, 38), anchor="lm")
    draw.text((100, 1800), "• Thức ăn đặc vón cục gây tắc nghẽn dạ dày, con sợ ăn cả đời!", font=f_tag_sub, fill=(185, 28, 28), anchor="lm")
    
    out_img = OUT_DIR / "scene_02.png"
    img.convert("RGB").save(out_img, quality=95)
    
    # Thứ tự: Hình dạ dày êm ái (1) -> Thẻ chữ sữa lỏng (2) -> Hình dạ dày quá tải (3) -> Thẻ chữ đạm đặc (4)
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s2_stomach_milk_visual",
                "label": "Hình Dạ Dày Sữa Lỏng",
                "region": {"x": 100, "y": 180, "width": 880, "height": 580},
                "reveal": {"startMs": 400, "durationMs": 2600}
            },
            {
                "id": "s2_card_milk",
                "label": "Thẻ Giải Thích Sữa Lỏng",
                "region": {"x": 60, "y": 780, "width": 960, "height": 150},
                "reveal": {"startMs": 3200, "durationMs": 1500}
            },
            {
                "id": "s2_stomach_clogged_visual",
                "label": "Hình Dạ Dày Bị Quá Tải",
                "region": {"x": 100, "y": 980, "width": 880, "height": 680},
                "reveal": {"startMs": 4900, "durationMs": 2800}
            },
            {
                "id": "s2_card_clogged",
                "label": "Thẻ Cảnh Báo Táo Bón Nôn Trớ",
                "region": {"x": 60, "y": 1680, "width": 960, "height": 180},
                "reveal": {"startMs": 7900, "durationMs": 1800}
            }
        ]
    }
    (OUT_DIR / "scene_02.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

# ==============================================================================
# SCENE 3: LỘ TRÌNH 3 NGÀY VÀNG (3 BÁT ĂN THỰC TẾ TRƯỚC -> THẺ CHỮ SAU)
# ==============================================================================
def compose_scene_3():
    print("Composing Scene 3 (3 Ngày vàng thực tế)...")
    img = Image.open(IMG3_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Header Banner
    draw_rounded_rect(draw, (60, 40, 1020, 140), radius=20, fill=(16, 185, 129, 245), outline=(255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 46)
    draw.text((540, 90), "🌟 3 NGÀY VÀNG KHỞI ĐỘNG KHOA HỌC", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Card 1 Overlay (Day 1)
    draw_rounded_rect(draw, (550, 200, 1030, 450), radius=18, fill=(255, 255, 255, 240), outline=(59, 130, 246), width=3)
    f_b_tag = get_font(FONT_BOLD, 30)
    f_b_head = get_font(FONT_BOLD, 34)
    f_b_sub = get_font(FONT_SEGOE_BOLD, 28)
    draw_rounded_rect(draw, (570, 220, 720, 265), radius=10, fill=(59, 130, 246))
    draw.text((645, 242), "NGÀY 1", font=f_b_tag, fill=(255, 255, 255), anchor="mm")
    draw.text((570, 300), "Cháo rây 1:10 loãng mịn", font=f_b_head, fill=(30, 64, 175), anchor="lm")
    draw.text((570, 360), "• Thử 1-2 thìa nhỏ làm quen", font=f_b_sub, fill=(55, 65, 81), anchor="lm")
    draw.text((570, 410), "• Độ loãng chuẩn như sữa mẹ", font=f_b_sub, fill=(55, 65, 81), anchor="lm")
    
    # 3. Card 2 Overlay (Day 2)
    draw_rounded_rect(draw, (550, 750, 1030, 1000), radius=18, fill=(255, 255, 255, 240), outline=(16, 185, 129), width=3)
    draw_rounded_rect(draw, (570, 770, 720, 815), radius=10, fill=(16, 185, 129))
    draw.text((645, 792), "NGÀY 2", font=f_b_tag, fill=(255, 255, 255), anchor="mm")
    draw.text((570, 850), "Cháo ngọt sữa mẹ", font=f_b_head, fill=(4, 120, 87), anchor="lm")
    draw.text((570, 910), "• Trộn thêm chút sữa quen", font=f_b_sub, fill=(55, 65, 81), anchor="lm")
    draw.text((570, 960), "• Giúp con hợp tác hào hứng", font=f_b_sub, fill=(55, 65, 81), anchor="lm")
    
    # 4. Card 3 Overlay (Day 3)
    draw_rounded_rect(draw, (550, 1350, 1030, 1600), radius=18, fill=(255, 255, 255, 240), outline=(249, 115, 22), width=3)
    draw_rounded_rect(draw, (570, 1370, 720, 1415), radius=10, fill=(249, 115, 22))
    draw.text((645, 1392), "NGÀY 3", font=f_b_tag, fill=(255, 255, 255), anchor="mm")
    draw.text((570, 1450), "Thêm 1 thìa bí đỏ rây", font=f_b_head, fill=(194, 65, 12), anchor="lm")
    draw.text((570, 1510), "• Bổ sung Vitamin A & chất xơ", font=f_b_sub, fill=(55, 65, 81), anchor="lm")
    draw.text((570, 1560), "• Vị ngọt bùi dễ tiêu hóa", font=f_b_sub, fill=(55, 65, 81), anchor="lm")
    
    out_img = OUT_DIR / "scene_03.png"
    img.convert("RGB").save(out_img, quality=95)
    
    # Thứ tự: Hình Bát 1 -> Thẻ 1 -> Hình Bát 2 -> Thẻ 2 -> Hình Bát 3 -> Thẻ 3
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s3_top_banner",
                "label": "Banner 3 Ngày Vàng Khởi Động",
                "region": {"x": 60, "y": 40, "width": 960, "height": 100},
                "reveal": {"startMs": 200, "durationMs": 1000}
            },
            {
                "id": "s3_bowl_day1_visual",
                "label": "Hình Bát Cháo Rây Ngày 1",
                "region": {"x": 50, "y": 160, "width": 500, "height": 500},
                "reveal": {"startMs": 1400, "durationMs": 2200}
            },
            {
                "id": "s3_card_day1",
                "label": "Thẻ Hướng Dẫn Ngày 1",
                "region": {"x": 550, "y": 200, "width": 480, "height": 250},
                "reveal": {"startMs": 2800, "durationMs": 1600}
            },
            {
                "id": "s3_bowl_day2_visual",
                "label": "Hình Bát Cháo Sữa Ngày 2",
                "region": {"x": 50, "y": 700, "width": 500, "height": 550},
                "reveal": {"startMs": 4600, "durationMs": 2200}
            },
            {
                "id": "s3_card_day2",
                "label": "Thẻ Hướng Dẫn Ngày 2",
                "region": {"x": 550, "y": 750, "width": 480, "height": 250},
                "reveal": {"startMs": 7000, "durationMs": 1600}
            },
            {
                "id": "s3_bowl_day3_visual",
                "label": "Hình Bát Bí Đỏ Ngày 3",
                "region": {"x": 50, "y": 1300, "width": 500, "height": 550},
                "reveal": {"startMs": 8800, "durationMs": 2200}
            },
            {
                "id": "s3_card_day3",
                "label": "Thẻ Hướng Dẫn Ngày 3",
                "region": {"x": 550, "y": 1350, "width": 480, "height": 250},
                "reveal": {"startMs": 11200, "durationMs": 1600}
            }
        ]
    }
    (OUT_DIR / "scene_03.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

# ==============================================================================
# SCENE 4: NGUYÊN TẮC VÀNG & CTA FOLLOW KÊNH
# ==============================================================================
def compose_scene_4():
    print("Composing Scene 4 (Nguyên tắc vàng & CTA)...")
    img = Image.open(IMG4_SRC).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    # 1. Top Header Banner
    draw_rounded_rect(draw, (60, 50, 1020, 155), radius=20, fill=(147, 51, 234, 245), outline=(255, 255, 255), width=3)
    f_title = get_font(FONT_BOLD, 44)
    draw.text((540, 102), "💡 3 NGUYÊN TẮC VÀNG TỪ CHUYÊN GIA", font=f_title, fill=(255, 255, 255), anchor="mm")
    
    # 2. Principles Card (Top)
    draw_rounded_rect(draw, (60, 175, 1020, 520), radius=20, fill=(255, 255, 255, 245), outline=(147, 51, 234), width=3)
    f_p_head = get_font(FONT_BOLD, 35)
    f_p_body = get_font(FONT_SEGOE_BOLD, 32)
    
    draw.text((100, 220), "MẸ GHI NHỚ NẰM LÒNG:", font=f_p_head, fill=(126, 34, 206), anchor="lm")
    draw.text((100, 290), "1. Ăn từ ít đến nhiều (1-2 thìa ➡️ nửa bát con)", font=f_p_body, fill=(31, 41, 55), anchor="lm")
    draw.text((100, 360), "2. Ăn từ loãng đến đặc (tập phản xạ nuốt thức ăn)", font=f_p_body, fill=(31, 41, 55), anchor="lm")
    draw.text((100, 435), "3. Tuyệt đối KHÔNG nêm mắm, muối, đường dưới 1 tuổi!", font=f_p_body, fill=(220, 38, 38), anchor="lm")
    
    # 3. Bottom CTA Card
    draw_rounded_rect(draw, (60, 1580, 1020, 1850), radius=24, fill=(236, 72, 153, 245), outline=(255, 255, 255), width=4)
    f_cta_1 = get_font(FONT_BOLD, 42)
    f_cta_2 = get_font(FONT_SEGOE_BOLD, 34)
    f_cta_3 = get_font(FONT_BOLD, 46)
    
    draw.text((540, 1640), "ĂN DẶM MẸ DÂU", font=f_cta_3, fill=(255, 255, 255), anchor="mm")
    draw.text((540, 1710), "Đồng hành nuôi con khoa học & nhàn tênh", font=f_cta_2, fill=(255, 241, 242), anchor="mm")
    draw.text((540, 1780), "❤️ Bấm Follow kênh để xem thực đơn Ngày 2 nhé!", font=f_cta_1, fill=(255, 255, 255), anchor="mm")
    
    out_img = OUT_DIR / "scene_04.png"
    img.convert("RGB").save(out_img, quality=95)
    
    # Thứ tự: Thẻ nguyên tắc (1) -> Hình mẹ cho bé ăn hạnh phúc (2) -> Thẻ CTA Follow (3)
    annotation = {
        "schemaVersion": 1,
        "canvas": {"width": 1080, "height": 1920},
        "background": {"color": "#F5EBD7"},
        "elements": [
            {
                "id": "s4_rules_card",
                "label": "Thẻ 3 Nguyên Tắc Vàng",
                "region": {"x": 60, "y": 50, "width": 960, "height": 470},
                "reveal": {"startMs": 400, "durationMs": 2400}
            },
            {
                "id": "s4_mom_baby_visual",
                "label": "Hình Mẹ Cho Bé Ăn Hợp Tác",
                "region": {"x": 50, "y": 550, "width": 980, "height": 980},
                "reveal": {"startMs": 3000, "durationMs": 2800}
            },
            {
                "id": "s4_cta_card",
                "label": "Thẻ Kêu Gọi Follow Kênh",
                "region": {"x": 60, "y": 1580, "width": 960, "height": 270},
                "reveal": {"startMs": 6000, "durationMs": 2000}
            }
        ]
    }
    (OUT_DIR / "scene_04.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_img

# ==============================================================================
# BUILD PROJECT.JSON & NARRATION CUES
# ==============================================================================
def build_project_json():
    project_data = {
        "schemaVersion": 1,
        "title": "Ăn Dặm Mẹ Dâu - Ngày 01: Cảnh Báo Sốc Y Khoa & 3 Ngày Vàng",
        "version": 1,
        "scenes": [
            {
                "id": "scene_01",
                "title": "Cảnh 1: Cảnh báo sốc thận non nớt và bát cháo thịt",
                "image": "scene_01.png",
                "annotation": "scene_01.annotation.json"
            },
            {
                "id": "scene_02",
                "title": "Cảnh 2: So sánh dạ dày sữa lỏng và đạm đặc",
                "image": "scene_02.png",
                "annotation": "scene_02.annotation.json"
            },
            {
                "id": "scene_03",
                "title": "Cảnh 3: Lộ trình 3 ngày vàng khởi động",
                "image": "scene_03.png",
                "annotation": "scene_03.annotation.json"
            },
            {
                "id": "scene_04",
                "title": "Cảnh 4: 3 Nguyên tắc vàng và CTA Follow",
                "image": "scene_04.png",
                "annotation": "scene_04.annotation.json"
            }
        ],
        "narration": [
            {
                "id": "cue_01",
                "sceneId": "scene_01",
                "text": "Dừng lại ngay! Mẹ có biết cho bé sáu tháng ăn cháo thịt bò hay chim bồ câu quá sớm là đang vô tình làm quá tải và tổn thương quả thận non nớt của con không?",
                "elementIds": ["s1_kidney_visual", "s1_meat_danger_visual", "s1_top_banner", "s1_bottom_alert_card"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 400
            },
            {
                "id": "cue_02",
                "sceneId": "scene_02",
                "text": "Tại sao ư? Vì hệ tiêu hóa của bé lúc này chỉ quen xử lý sữa lỏng mịn màng.",
                "elementIds": ["s2_stomach_milk_visual", "s2_card_milk"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_03",
                "sceneId": "scene_02",
                "text": "Ép con ăn đạm đặc quá sớm sẽ khiến dạ dày bị quá tải, gây trào ngược, nôn trớ, táo bón dữ dội và sợ ăn dặm kéo dài!",
                "elementIds": ["s2_stomach_clogged_visual", "s2_card_clogged"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 400
            },
            {
                "id": "cue_04",
                "sceneId": "scene_03",
                "text": "Thay vào đó, mẹ hãy bắt đầu chuẩn chỉnh với ba ngày vàng khoa học này nhé:",
                "elementIds": ["s3_top_banner"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_05",
                "sceneId": "scene_03",
                "text": "Ngày một: Thử một đến hai thìa cháo rây tỉ lệ một mười, nấu thật loãng và mịn như dòng sữa mẹ.",
                "elementIds": ["s3_bowl_day1_visual", "s3_card_day1"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_06",
                "sceneId": "scene_03",
                "text": "Ngày hai: Trộn thêm chút sữa mẹ để tạo hương vị quen thuộc giúp con hào hứng hợp tác.",
                "elementIds": ["s3_bowl_day2_visual", "s3_card_day2"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_07",
                "sceneId": "scene_03",
                "text": "Ngày ba: Thêm một thìa nhỏ bí đỏ rây nhuyễn để bổ sung vitamin A và chất xơ tự nhiên!",
                "elementIds": ["s3_bowl_day3_visual", "s3_card_day3"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 400
            },
            {
                "id": "cue_08",
                "sceneId": "scene_04",
                "text": "Mẹ ghi nhớ ba nguyên tắc: Ăn từ ít đến nhiều, từ loãng đến đặc và tuyệt đối không nêm mắm muối gia vị dưới một tuổi!",
                "elementIds": ["s4_rules_card", "s4_mom_baby_visual"],
                "pauseBeforeMs": 200,
                "pauseAfterMs": 300
            },
            {
                "id": "cue_09",
                "sceneId": "scene_04",
                "text": "Lưu lại ngay video này và bấm Follow kênh Ăn dặm mẹ Dâu để nhận trọn bộ thực đơn ba mươi ngày khoa học nhé!",
                "elementIds": ["s4_cta_card"],
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
    compose_scene_4()
    build_project_json()
    print("Project build v2 ready in:", OUT_DIR)
