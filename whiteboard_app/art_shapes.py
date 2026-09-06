import math
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "arialbd.ttf"
FONT_REGULAR = "arial.ttf"

THEME_COLOR = (225, 112, 30)      # Cam ấm mẹ Dâu
RED_COLOR = (217, 83, 79)         # Đỏ cảnh báo y khoa
GREEN_COLOR = (46, 204, 113)      # Xanh lá tiêu hóa tốt
BLUE_COLOR = (52, 152, 219)       # Xanh dương
DARK_TEXT = (40, 30, 20)          # Xám đậm chữ đọc
PAPER_BG = (245, 235, 215)        # Nền giấy kem #F5EBD7

def get_font(name, size):
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()

# ==============================================================================
# 1. CÁC HÌNH KHỐI NGHỆ THUẬT VẼ TAY (ARTISTIC GRAPHIC SHAPES)
# ==============================================================================

def draw_vector_heart(draw, cx, cy, size=20, fill=(255, 255, 255), outline=None):
    """Trái tim vector toán học chuẩn xác, mượt mà không lỗi font emoji."""
    pts = []
    scale = size / 16.0
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = cx + scale * 16 * (math.sin(rad) ** 3)
        y = cy - scale * (13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad))
        pts.append((x, y))
    draw.polygon(pts, fill=fill, outline=outline)

def draw_vector_sun(draw, cx, cy, radius=14, fill=(243, 156, 18)):
    """Hình vẽ ông mặt trời vector nhỏ xinh."""
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill)
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        x1 = cx + (radius + 4) * math.cos(angle)
        y1 = cy + (radius + 4) * math.sin(angle)
        x2 = cx + (radius + 10) * math.cos(angle)
        y2 = cy + (radius + 10) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=fill, width=3)

def draw_vector_spoon(draw, cx, cy, fill=(180, 130, 80)):
    """Hình chiếc thìa nhỏ vector."""
    # Bầu thìa
    draw.ellipse((cx - 18, cy - 10, cx - 4, cy + 10), fill=fill)
    # Cán thìa
    draw.line([(cx - 5, cy), (cx + 18, cy)], fill=fill, width=4)

def draw_vector_calendar(draw, cx, cy, fill=BLUE_COLOR):
    """Hình cuốn lịch vector nhỏ."""
    draw.rounded_rectangle((cx - 14, cy - 14, cx + 14, cy + 14), radius=4, fill=(255, 255, 255), outline=fill, width=2)
    draw.rectangle((cx - 14, cy - 14, cx + 14, cy - 6), fill=fill)
    f_num = get_font(FONT_BOLD, 14)
    draw.text((cx, cy + 3), "3", font=f_num, fill=fill, anchor="mm")

def wrap_text(draw, text, font, max_width):
    """Tự động ngắt dòng thông minh theo độ rộng khung, trả về danh sách các dòng."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_ribbon_banner(draw, bbox, fill=THEME_COLOR, outline=(40, 25, 15), text="", font_path=FONT_BOLD, max_font_size=40, text_fill=(255, 255, 255)):
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
        max_text_w = w - 130  # Đảm bảo lề đệm >= 60px ở mỗi đầu
        font_size = max_font_size
        font = get_font(font_path, font_size)
        t_bbox = draw.textbbox((0, 0), text, font=font)
        while (t_bbox[2] - t_bbox[0]) > max_text_w and font_size > 22:
            font_size -= 2
            font = get_font(font_path, font_size)
            t_bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((x0 + x1) / 2, (y0 + y1) / 2 - 2), text, font=font, fill=text_fill, anchor="mm")

def draw_speech_bubble(draw, bbox, tail_point, fill=(255, 255, 255, 248), outline=RED_COLOR, radius=26, width=3):
    """Bóng thoại comic có đuôi chỉ thẳng vào đối tượng (đuôi đệm an toàn)."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)
    tx, ty = tail_point
    base_x = (x0 + x1) / 2
    if ty > y1:
        tail_poly = [(base_x - 30, y1 - 2), (base_x + 10, y1 - 2), (tx, ty)]
    else:
        tail_poly = [(base_x - 30, y0 + 2), (base_x + 10, y0 + 2), (tx, ty)]
    draw.polygon(tail_poly, fill=fill)
    draw.line([tail_poly[0], (tx, ty), tail_poly[1]], fill=outline, width=width)
    if ty > y1:
        draw.line([(base_x - 28, y1), (base_x + 8, y1)], fill=fill, width=width + 2)
    else:
        draw.line([(base_x - 28, y0), (base_x + 8, y0)], fill=fill, width=width + 2)

def draw_washi_memo_card(draw, bbox, fill=(255, 255, 255, 248), outline=GREEN_COLOR, tape_color=(245, 170, 110), width=3):
    """Tờ ghi chú memo có dán băng dính washi tape ở đỉnh."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=20, fill=fill, outline=outline, width=width)
    tape_w = 150
    tape_h = 36
    tx0 = (x0 + x1) / 2 - tape_w / 2
    tx1 = (x0 + x1) / 2 + tape_w / 2
    ty0 = y0 - tape_h / 2
    ty1 = y0 + tape_h / 2
    draw.polygon([(tx0, ty0 + 3), (tx1, ty0 - 3), (tx1, ty1 - 3), (tx0, ty1 + 3)], fill=tape_color)
    draw.line([(tx0, ty0 + 3), (tx1, ty0 - 3), (tx1, ty1 - 3), (tx0, ty1 + 3), (tx0, ty0 + 3)], fill=(180, 120, 60), width=1)

def draw_step_pill_badge(draw, x, y, step_num, title, desc, tag_text="", theme_color=THEME_COLOR, card_width=None):
    """Huy hiệu bước thực hành bo góc cao cấp: tự tính toán auto-fit, không bao giờ tràn viền."""
    circle_r = 40
    cx = x + circle_r
    cy = y + circle_r
    draw.ellipse((cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r), fill=theme_color, outline=(255, 255, 255), width=3)
    f_num = get_font(FONT_BOLD, 42)
    draw.text((cx, cy - 2), str(step_num), font=f_num, fill=(255, 255, 255), anchor="mm")

    card_x0 = x + circle_r * 2 + 12
    card_y0 = y
    if card_width is not None:
        card_x1 = card_x0 + card_width
    else:
        card_x1 = x + 980
    
    is_compact = (card_width is not None and card_width < 600)
    card_y1 = y + (175 if is_compact else 135)
    draw.rounded_rectangle((card_x0, card_y0, card_x1, card_y1), radius=20, fill=(255, 255, 255, 248), outline=theme_color, width=3)

    inner_pad = 18
    # Vẽ tag nếu có: Trên card compact, tag pill được đặt ở góc trên phải hoặc tách bạch an toàn
    tag_w = 0
    if tag_text:
        f_tag = get_font(FONT_BOLD, 18 if is_compact else 24)
        t_bb = draw.textbbox((0, 0), tag_text, font=f_tag)
        tag_w = (t_bb[2] - t_bb[0]) + 20
        tag_h = 28 if is_compact else 38
        tx1 = card_x1 - inner_pad
        tx0 = tx1 - tag_w
        ty0 = card_y0 + (10 if is_compact else 12)
        ty1 = ty0 + tag_h
        draw.rounded_rectangle((tx0, ty0, tx1, ty1), radius=14, fill=theme_color, outline=(255, 255, 255), width=2)
        draw.text(((tx0 + tx1) / 2, (ty0 + ty1) / 2 - 1), tag_text, font=f_tag, fill=(255, 255, 255), anchor="mm")

    # Tính toán tiêu đề auto-fit trong không gian còn lại (chừa khoảng đệm an toàn tới tag)
    gap_to_tag = (tag_w + 16) if tag_text else 0
    max_title_w = (card_x1 - inner_pad - gap_to_tag) - (card_x0 + inner_pad)
    f_title_size = 24 if is_compact else 34
    f_title = get_font(FONT_BOLD, f_title_size)
    t_bbox = draw.textbbox((0, 0), title, font=f_title)
    while (t_bbox[2] - t_bbox[0]) > max_title_w and f_title_size > 16:
        f_title_size -= 1
        f_title = get_font(FONT_BOLD, f_title_size)
        t_bbox = draw.textbbox((0, 0), title, font=f_title)
    draw.text((card_x0 + inner_pad, card_y0 + (24 if is_compact else 34)), title, font=f_title, fill=theme_color, anchor="lm")

    # Nội dung mô tả (desc): Tự động wrap thông minh không bao giờ tràn viền
    f_desc_size = 22 if is_compact else 26
    f_desc = get_font(FONT_BOLD, f_desc_size)
    max_desc_w = (card_x1 - card_x0) - inner_pad * 2 - 10

    if isinstance(desc, list):
        desc_lines = desc
    elif "\n" in desc:
        desc_lines = desc.split("\n")
    else:
        desc_lines = [desc]

    curr_y = card_y0 + 72
    for item in desc_lines:
        item_str = item.strip()
        if not item_str.startswith("•") and not item_str.startswith("-"):
            item_str = "• " + item_str
        wrapped = wrap_text(draw, item_str, f_desc, max_desc_w)
        for w_line in wrapped:
            draw.text((card_x0 + inner_pad, curr_y), w_line, font=f_desc, fill=(50, 50, 50), anchor="lm")
            curr_y += 34

def draw_cta_capsule(draw, bbox, title="BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!", subtext="Đồng hành chăm con khỏe mạnh chuẩn y khoa", fill=THEME_COLOR):
    """Khối CTA bo tròn viên nang có auto-fit và icon trái tim cách đều an toàn."""
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    draw.rounded_rectangle(bbox, radius=45, fill=fill, outline=(255, 255, 255), width=3)

    max_w = (x1 - x0) - 180
    f_size = 36
    font_head = get_font(FONT_BOLD, f_size)
    t_bbox = draw.textbbox((0, 0), title, font=font_head)
    while (t_bbox[2] - t_bbox[0]) > max_w and f_size > 22:
        f_size -= 2
        font_head = get_font(FONT_BOLD, f_size)
        t_bbox = draw.textbbox((0, 0), title, font=font_head)

    tw = t_bbox[2] - t_bbox[0]
    draw.text((cx, y0 + 52), title, font=font_head, fill=(255, 255, 255), anchor="mm")

    left_heart_x = cx - tw / 2 - 38
    right_heart_x = cx + tw / 2 + 38
    draw_vector_heart(draw, left_heart_x, y0 + 52, size=18, fill=(255, 255, 255), outline=None)
    draw_vector_heart(draw, right_heart_x, y0 + 52, size=18, fill=(255, 255, 255), outline=None)

    font_sub = get_font(FONT_BOLD, 26)
    draw.text((cx, y0 + 112), subtext, font=font_sub, fill=(255, 255, 255), anchor="mm")

# ==============================================================================
# 2. CÁC BIỂU TƯỢNG VÀ HÌNH MINH HỌA DOODLE VECTOR THEO KỊCH BẢN (KHÔNG DÙNG EMOJI FONT)
# ==============================================================================

def draw_prohibition_badge(draw, cx, cy, radius=35):
    """Biểu tượng cấm màu đỏ 🚫 vẽ vector trực tiếp."""
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(255, 255, 255), outline=RED_COLOR, width=5)
    rad = math.radians(45)
    dx = radius * math.cos(rad)
    dy = radius * math.sin(rad)
    draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=RED_COLOR, width=5)

def draw_egg_size_badge(draw, cx, cy):
    """Minh họa quả trứng gà so sánh kích thước dạ dày bé 6 tháng có auto-fit chống đè chữ."""
    f1 = get_font(FONT_BOLD, 23)
    f2 = get_font(FONT_REGULAR, 19)
    txt1 = "DẠ DÀY = QUẢ TRỨNG"
    txt2 = "Dung tích nhỏ ~ 30-50ml"
    bb1 = draw.textbbox((0, 0), txt1, font=f1)
    bb2 = draw.textbbox((0, 0), txt2, font=f2)
    text_w = max(bb1[2] - bb1[0], bb2[2] - bb2[0])
    
    # Khoảng cách an toàn: egg_w (50px) + padding (30px) + text_w + right_pad (30px)
    half_w = max(195, int((50 + 30 + text_w + 30) / 2))
    draw.rounded_rectangle((cx - half_w, cy - 45, cx + half_w, cy + 45), radius=22, fill=(255, 255, 255, 245), outline=GREEN_COLOR, width=2)
    
    # Vẽ quả trứng gà vector ở góc trái an toàn
    egg_x = cx - half_w + 35
    draw.ellipse((egg_x - 18, cy - 24, egg_x + 18, cy + 24), fill=(255, 224, 178), outline=(180, 120, 60), width=2)
    
    # Canh chữ bắt đầu từ sau quả trứng
    text_center_x = egg_x + 28 + text_w / 2
    draw.text((text_center_x, cy - 12), txt1, font=f1, fill=GREEN_COLOR, anchor="mm")
    draw.text((text_center_x, cy + 15), txt2, font=f2, fill=(80, 80, 80), anchor="mm")

def draw_scale_icon(draw, cx, cy, label="10g", sub="CÂN TIỂU LY"):
    """Biểu tượng cân tiểu ly định lượng gram chuẩn có auto-fit."""
    f_num = get_font(FONT_BOLD, 22)
    f_sub = get_font(FONT_BOLD, 17)
    bb_main = draw.textbbox((0, 0), label, font=f_num)
    bb_sub = draw.textbbox((0, 0), sub, font=f_sub)
    w = max(bb_main[2] - bb_main[0], bb_sub[2] - bb_sub[0]) + 36
    half_w = max(80, int(w / 2))
    draw.rounded_rectangle((cx - half_w, cy - 35, cx + half_w, cy + 35), radius=16, fill=(255, 255, 255), outline=THEME_COLOR, width=2)
    draw.rectangle((cx - half_w + 14, cy - 22, cx + half_w - 14, cy + 5), fill=(235, 245, 255), outline=(100, 150, 200), width=1)
    draw.text((cx, cy - 8), label, font=f_num, fill=(20, 80, 160), anchor="mm")
    draw.text((cx, cy + 20), sub, font=f_sub, fill=THEME_COLOR, anchor="mm")

def draw_beaker_water(draw, cx, cy, label="100ml", sub="NƯỚC LỌC"):
    """Biểu tượng cốc đong nước có vạch mức có auto-fit."""
    f_num = get_font(FONT_BOLD, 22)
    f_sub = get_font(FONT_BOLD, 16)
    bb_main = draw.textbbox((0, 0), label, font=f_num)
    bb_sub = draw.textbbox((0, 0), sub, font=f_sub)
    text_w = max(bb_main[2] - bb_main[0], bb_sub[2] - bb_sub[0])
    half_w = max(90, int((45 + text_w + 30) / 2))
    draw.rounded_rectangle((cx - half_w, cy - 35, cx + half_w, cy + 35), radius=16, fill=(255, 255, 255), outline=(41, 128, 185), width=2)
    
    icon_cx = cx - half_w + 25
    pts = [(icon_cx - 10, cy - 10), (icon_cx, cy + 10), (icon_cx - 20, cy + 10)]
    draw.polygon(pts, fill=(52, 152, 219))
    draw.ellipse((icon_cx - 20, cy - 2, icon_cx, cy + 18), fill=(52, 152, 219))
    
    text_cx = icon_cx + 20 + text_w / 2
    draw.text((text_cx, cy - 10), label, font=f_num, fill=(41, 128, 185), anchor="mm")
    draw.text((text_cx, cy + 18), sub, font=f_sub, fill=(100, 100, 100), anchor="mm")

def draw_clock_timer(draw, cx, cy, label="45 PHÚT", sub="NINH NHỎ LỬA"):
    """Biểu tượng đồng hồ hẹn giờ ninh nhỏ lửa có auto-fit."""
    f_lbl = get_font(FONT_BOLD, 21)
    f_sub = get_font(FONT_BOLD, 16)
    bb_lbl = draw.textbbox((0, 0), label, font=f_lbl)
    bb_sub = draw.textbbox((0, 0), sub, font=f_sub)
    text_w = max(bb_lbl[2] - bb_lbl[0], bb_sub[2] - bb_sub[0])
    half_w = max(100, int((45 + text_w + 32) / 2))
    draw.rounded_rectangle((cx - half_w, cy - 35, cx + half_w, cy + 35), radius=16, fill=(255, 255, 255), outline=THEME_COLOR, width=2)
    
    clock_x = cx - half_w + 25
    draw.ellipse((clock_x - 16, cy - 16, clock_x + 16, cy + 16), fill=(255, 243, 224), outline=THEME_COLOR, width=2)
    draw.line([(clock_x, cy), (clock_x, cy - 9)], fill=THEME_COLOR, width=2)
    draw.line([(clock_x, cy), (clock_x + 7, cy)], fill=THEME_COLOR, width=2)
    
    text_cx = clock_x + 22 + text_w / 2
    draw.text((text_cx, cy - 10), label, font=f_lbl, fill=THEME_COLOR, anchor="mm")
    draw.text((text_cx, cy + 16), sub, font=f_sub, fill=(180, 50, 20), anchor="mm")

def draw_sieve_badge(draw, cx, cy, label="LƯỚI 0.5MM", sub="MIẾT THÌA 2 LẦN"):
    """Biểu tượng rây mịn và miết lưng thìa 2 lần có auto-fit."""
    f_main = get_font(FONT_BOLD, 21)
    f_sub = get_font(FONT_BOLD, 16)
    bb_lbl = draw.textbbox((0, 0), label, font=f_main)
    bb_sub = draw.textbbox((0, 0), sub, font=f_sub)
    text_w = max(bb_lbl[2] - bb_lbl[0], bb_sub[2] - bb_sub[0])
    half_w = max(110, int((45 + text_w + 32) / 2))
    draw.rounded_rectangle((cx - half_w, cy - 35, cx + half_w, cy + 35), radius=16, fill=(255, 255, 255), outline=(46, 204, 113), width=2)
    
    sieve_x = cx - half_w + 25
    draw.ellipse((sieve_x - 16, cy - 15, sieve_x + 16, cy + 15), fill=(46, 204, 113))
    draw.line([(sieve_x - 8, cy), (sieve_x - 2, cy + 6), (sieve_x + 8, cy - 5)], fill=(255, 255, 255), width=3)
    
    text_cx = sieve_x + 22 + text_w / 2
    draw.text((text_cx, cy - 10), label, font=f_main, fill=(39, 174, 96), anchor="mm")
    draw.text((text_cx, cy + 16), sub, font=f_sub, fill=(60, 60, 60), anchor="mm")

def draw_spoon_dosage(draw, cx, cy, label="1 - 2 THÌA CÀ PHÊ (5ML)"):
    """Biểu tượng liều lượng nếm thử thìa nhỏ 5ml có hình vector chiếc thìa."""
    draw.rounded_rectangle((cx - 380, cy - 48, cx + 380, cy + 48), radius=24, fill=(255, 255, 255, 248), outline=THEME_COLOR, width=3)
    draw_vector_spoon(draw, cx - 280, cy, fill=THEME_COLOR)
    f1 = get_font(FONT_BOLD, 30)
    f2 = get_font(FONT_REGULAR, 24)
    draw.text((cx + 30, cy - 16), label, font=f1, fill=THEME_COLOR, anchor="mm")
    draw.text((cx + 30, cy + 20), "Chỉ nếm vị, không ép ăn hết bát", font=f2, fill=(70, 70, 70), anchor="mm")

def draw_sun_time_badge(draw, cx, cy, label="CỮ SÁNG: 9H - 10H"):
    """Biểu tượng thời điểm ăn dặm cữ sáng có hình vẽ mặt trời vector."""
    draw.rounded_rectangle((cx - 380, cy - 48, cx + 380, cy + 48), radius=24, fill=(255, 255, 255, 248), outline=(243, 156, 18), width=3)
    draw_vector_sun(draw, cx - 280, cy, radius=16, fill=(243, 156, 18))
    f1 = get_font(FONT_BOLD, 30)
    f2 = get_font(FONT_REGULAR, 24)
    draw.text((cx + 30, cy - 16), label, font=f1, fill=(211, 84, 0), anchor="mm")
    draw.text((cx + 30, cy + 20), "Con tỉnh táo, bụng dễ chịu nhất", font=f2, fill=(70, 70, 70), anchor="mm")

def draw_calendar_allergy_badge(draw, cx, cy, label="QUY TẮC 3 NGÀY"):
    """Biểu tượng cuốn lịch vector theo dõi dị ứng thức ăn mới."""
    draw.rounded_rectangle((cx - 380, cy - 48, cx + 380, cy + 48), radius=24, fill=(255, 255, 255, 248), outline=BLUE_COLOR, width=3)
    # Lịch vector rõ ràng hơn
    draw.rounded_rectangle((cx - 300, cy - 22, cx - 260, cy + 22), radius=6, fill=(255, 255, 255), outline=BLUE_COLOR, width=2)
    draw.rectangle((cx - 300, cy - 22, cx - 260, cy - 8), fill=BLUE_COLOR)
    f_num = get_font(FONT_BOLD, 20)
    draw.text((cx - 280, cy + 8), "3", font=f_num, fill=BLUE_COLOR, anchor="mm")
    f1 = get_font(FONT_BOLD, 30)
    f2 = get_font(FONT_REGULAR, 24)
    draw.text((cx + 30, cy - 16), label, font=f1, fill=(41, 128, 185), anchor="mm")
    draw.text((cx + 30, cy + 20), "Theo dõi phân & da trước khi đổi món", font=f2, fill=(70, 70, 70), anchor="mm")
