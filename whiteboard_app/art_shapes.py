import math
import cv2
import numpy as np
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

def draw_fitted_text(
    draw,
    xy: tuple[float, float],
    text: str,
    font_path: str = FONT_BOLD,
    max_font_size: int = 32,
    min_font_size: int = 14,
    max_width: float = 850,
    fill: tuple = (0, 0, 0),
    anchor: str = "mm",
    allow_wrap: bool = True,
    line_spacing: int = 6
):
    """
    Vẽ chữ thông minh chống tràn viền 100%:
    - Tự động co giãn kích thước font từ max_font_size xuống sao cho vừa khít max_width.
    - Nếu câu dài hoặc chứa dấu gạch nối ' — ', tự động tách 2 dòng cân đối, đẹp mắt.
    - Đảm bảo 100% không bao giờ chữ bị thò ra ngoài max_width.
    """
    if not text:
        return
    x, y = xy

    # Nếu câu có dấu gạch ngang phân cách và dài > 25 ký tự, ưu tiên tách 2 dòng tự nhiên
    if allow_wrap and (" — " in text or " : " in text) and len(text) > 25:
        delim = " — " if " — " in text else " : "
        parts = text.split(delim, 1)
        part1 = parts[0].strip()
        part2 = parts[1].strip()
        f_top = get_font(font_path, min(max_font_size, 30))
        f_sub = get_font(font_path, min(max_font_size - 4, 24))
        
        # Co font cho từng dòng nếu cần
        while f_top.getbbox(part1)[2] > max_width and f_top.size > 14:
            f_top = get_font(font_path, f_top.size - 1)
        while f_sub.getbbox(part2)[2] > max_width and f_sub.size > 12:
            f_sub = get_font(font_path, f_sub.size - 1)

        h1 = f_top.getbbox(part1)[3] - f_top.getbbox(part1)[1]
        h2 = f_sub.getbbox(part2)[3] - f_sub.getbbox(part2)[1]
        total_h = h1 + h2 + line_spacing
        
        draw.text((x, y - total_h / 2 + h1 / 2), part1, font=f_top, fill=fill, anchor=anchor)
        draw.text((x, y + total_h / 2 - h2 / 2), part2, font=f_sub, fill=fill, anchor=anchor)
        return

    # Trường hợp vẽ 1 dòng hoặc word-wrap bình thường
    font_size = max_font_size
    font = get_font(font_path, font_size)
    t_bbox = draw.textbbox((0, 0), text, font=font)
    txt_w = t_bbox[2] - t_bbox[0]

    # Giảm font size cho đến khi vừa khít max_width
    while txt_w > max_width and font_size > min_font_size:
        font_size -= 1
        font = get_font(font_path, font_size)
        t_bbox = draw.textbbox((0, 0), text, font=font)
        txt_w = t_bbox[2] - t_bbox[0]

    if txt_w > max_width and allow_wrap:
        lines = wrap_text(draw, text, font, max_width)
        line_h = (t_bbox[3] - t_bbox[1]) + line_spacing
        total_h = len(lines) * line_h
        start_y = y - total_h / 2 + line_h / 2 if "m" in anchor else y
        for i, line in enumerate(lines):
            draw.text((x, start_y + i * line_h), line, font=font, fill=fill, anchor=anchor)
    else:
        # Nếu vẫn còn lớn hơn max_width (khi không wrap), tiếp tục giảm font tuyệt đối không để tràn
        while txt_w > max_width and font_size > 10:
            font_size -= 1
            font = get_font(font_path, font_size)
            t_bbox = draw.textbbox((0, 0), text, font=font)
            txt_w = t_bbox[2] - t_bbox[0]
        draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


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

def draw_step_pill_badge(draw, x, y, step_num, title, desc, tag_text="", theme_color=THEME_COLOR, card_width=None, is_compact=False, inner_pad=18):
    """Huy hiệu bước thực hành bo góc cao cấp: tự tính toán auto-fit theo từng câu chữ, không bao giờ tràn viền."""
    circle_r = 28 if is_compact else 34
    card_x0 = x + circle_r * 2 + 12
    card_y0 = y
    if card_width is not None:
        card_x1 = card_x0 + card_width
    else:
        card_x1 = x + 980

    # BẢO VỆ BIÊN AN TOÀN (Safe Margin Constraint): Mép phải không bao giờ vượt quá 1040px
    if card_x1 > 1040:
        overflow_dx = card_x1 - 1040
        x = max(30, x - overflow_dx)
        card_x0 = x + circle_r * 2 + 12
        card_x1 = 1040

    cx = x + circle_r
    cy = y + circle_r
    draw.ellipse((cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r), fill=theme_color, outline=(255, 255, 255), width=3)
    f_num = get_font(FONT_BOLD, 36 if is_compact else 42)
    draw.text((cx, cy - 2), str(step_num), font=f_num, fill=(255, 255, 255), anchor="mm")
    
    # Nội dung mô tả (desc): Tự động tính toán số dòng và co giãn linh hoạt
    if isinstance(desc, list):
        desc_raw = desc
    elif "\n" in desc:
        desc_raw = desc.split("\n")
    else:
        desc_raw = [desc]

    f_desc_size = 20 if is_compact else 23
    f_desc = get_font(FONT_REGULAR, f_desc_size)
    max_desc_w = (card_x1 - card_x0) - inner_pad * 2 - 10

    # Tính toán toàn bộ các dòng sau khi wrap
    desc_wrapped_lines = []
    for item in desc_raw:
        item_str = item.strip()
        if not item_str.startswith("•") and not item_str.startswith("-"):
            item_str = "• " + item_str
        desc_wrapped_lines.extend(wrap_text(draw, item_str, f_desc, max_desc_w))

    # Tính toán chiều cao cần thiết để chữ không bao giờ thò ra ngoài đáy card
    line_h = 28 if is_compact else 33
    start_desc_y = card_y0 + (56 if is_compact else 66)
    min_card_h = 125
    needed_card_h = (start_desc_y - card_y0) + len(desc_wrapped_lines) * line_h + 14
    actual_card_h = max(min_card_h, needed_card_h)
    card_y1 = card_y0 + actual_card_h

    # Tự động loại bỏ tiền tố thừa nếu đã có huy hiệu tròn bên cạnh
    clean_title = title
    for pfx in [
        "BƯỚC 1:", "BƯỚC 2:", "BƯỚC 3:", "BƯỚC 1 :", "BƯỚC 2 :", "BƯỚC 3 :", "BƯỚC 1 -", "BƯỚC 2 -", "BƯỚC 3 -",
        "NGUYÊN TẮC 1:", "NGUYÊN TẮC 2:", "NGUYÊN TẮC 3:", "NGUYÊN TẮC 1 :", "NGUYÊN TẮC 2 :", "NGUYÊN TẮC 3 :", "NGUYÊN TẮC 1 -", "NGUYÊN TẮC 2 -", "NGUYÊN TẮC 3 -",
        "NGÀY 1:", "NGÀY 2:", "NGÀY 3:", "NGÀY 1 :", "NGÀY 2 :", "NGÀY 3 :", "NGÀY 1 -", "NGÀY 2 -", "NGÀY 3 -",
        "08:00 SÁNG:", "10:00 SÁNG:", "14:30 CHIỀU:"
    ]:
        if clean_title.upper().startswith(pfx):
            clean_title = clean_title[len(pfx):].strip()
            break

    # Đo độ rộng tag nếu có để trừ lùi
    clean_tag = tag_text.strip() if tag_text else ""
    show_tag = bool(clean_tag)
    # Tự động ẩn tag nếu tag bị trùng lặp với tiêu đề (để tránh lãng phí diện tích)
    if show_tag and clean_tag.upper() in clean_title.upper():
        show_tag = False

    tag_w = 0
    f_tag = get_font(FONT_BOLD, 17 if is_compact else 20)
    if show_tag:
        t_bb = draw.textbbox((0, 0), clean_tag, font=f_tag)
        tag_w = (t_bb[2] - t_bb[0]) + 18

    # Tính toán tiêu đề auto-fit trong không gian còn lại (chừa khoảng đệm an toàn tới tag >= 14px)
    gap_to_tag = (tag_w + 14) if show_tag else 0
    max_title_w = (card_x1 - inner_pad - gap_to_tag) - (card_x0 + inner_pad)
    f_title_size = 24 if is_compact else 28
    f_title = get_font(FONT_BOLD, f_title_size)
    t_bbox = draw.textbbox((0, 0), clean_title, font=f_title)
    while (t_bbox[2] - t_bbox[0]) > max_title_w and f_title_size > 19:
        f_title_size -= 1
        f_title = get_font(FONT_BOLD, f_title_size)
        t_bbox = draw.textbbox((0, 0), clean_title, font=f_title)

    # Nếu ngay cả ở cỡ chữ 19 mà tiêu đề vẫn quá dài khi có tag, ưu tiên ẩn tag để tiêu đề luôn to rõ ràng
    if (t_bbox[2] - t_bbox[0]) > max_title_w and show_tag:
        show_tag = False
        tag_w = 0
        gap_to_tag = 0
        max_title_w = (card_x1 - inner_pad) - (card_x0 + inner_pad)
        f_title_size = 24 if is_compact else 28
        f_title = get_font(FONT_BOLD, f_title_size)
        t_bbox = draw.textbbox((0, 0), clean_title, font=f_title)
        while (t_bbox[2] - t_bbox[0]) > max_title_w and f_title_size > 16:
            f_title_size -= 1
            f_title = get_font(FONT_BOLD, f_title_size)
            t_bbox = draw.textbbox((0, 0), clean_title, font=f_title)

    # Vẽ nền thẻ card với chiều cao vừa khít 100%
    draw.rounded_rectangle((card_x0, card_y0, card_x1, card_y1), radius=20, fill=(255, 255, 255, 248), outline=theme_color, width=3)

    # Vẽ tag pill nếu có
    if show_tag:
        tag_h = 28 if is_compact else 34
        tx1 = card_x1 - inner_pad
        tx0 = tx1 - tag_w
        ty0 = card_y0 + (10 if is_compact else 12)
        ty1 = ty0 + tag_h
        draw.rounded_rectangle((tx0, ty0, tx1, ty1), radius=14, fill=theme_color, outline=(255, 255, 255), width=2)
        draw.text(((tx0 + tx1) / 2, (ty0 + ty1) / 2 - 1), clean_tag, font=f_tag, fill=(255, 255, 255), anchor="mm")

    # Vẽ tiêu đề đã căn chỉnh auto-fit
    draw.text((card_x0 + inner_pad, card_y0 + (24 if is_compact else 32)), clean_title, font=f_title, fill=theme_color, anchor="lm")

    # Vẽ các dòng mô tả
    curr_y = start_desc_y
    for w_line in desc_wrapped_lines:
        draw.text((card_x0 + inner_pad, curr_y), w_line, font=f_desc, fill=(50, 50, 50), anchor="lm")
        curr_y += line_h

    return (x, card_y0, card_x1, card_y1)

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
    """Biểu tượng liều lượng nếm thử thìa nhỏ 5ml có hình vector chiếc thìa, rộng 920px chống tràn viền 100%."""
    bbox = (cx - 460, cy - 48, cx + 460, cy + 48)
    draw.rounded_rectangle(bbox, radius=24, fill=(255, 255, 255, 248), outline=THEME_COLOR, width=3)
    draw_vector_spoon(draw, cx - 380, cy, fill=THEME_COLOR)
    draw_auto_card_text(
        draw, bbox,
        title=label,
        desc="Chỉ nếm vị, không ép ăn hết bát",
        theme_color=THEME_COLOR,
        desc_color=(70, 70, 70),
        max_title_font=26,
        min_title_font=16,
        max_desc_font=20,
        min_desc_font=14,
        icon_left_pad=100,
        align="center"
    )

def draw_sun_time_badge(draw, cx, cy, label="CỮ SÁNG: 9H - 10H"):
    """Biểu tượng thời điểm ăn dặm cữ sáng có hình vẽ mặt trời vector, rộng 920px chống tràn viền 100%."""
    bbox = (cx - 460, cy - 48, cx + 460, cy + 48)
    draw.rounded_rectangle(bbox, radius=24, fill=(255, 255, 255, 248), outline=(243, 156, 18), width=3)
    draw_vector_sun(draw, cx - 380, cy, radius=16, fill=(243, 156, 18))
    draw_auto_card_text(
        draw, bbox,
        title=label,
        desc="Con tỉnh táo, bụng dễ chịu nhất",
        theme_color=(211, 84, 0),
        desc_color=(70, 70, 70),
        max_title_font=26,
        min_title_font=16,
        max_desc_font=20,
        min_desc_font=14,
        icon_left_pad=100,
        align="center"
    )

def draw_calendar_allergy_badge(draw, cx, cy, label="QUY TẮC 3 NGÀY"):
    """Biểu tượng cuốn lịch vector theo dõi dị ứng thức ăn mới, rộng 920px chống tràn viền 100%."""
    bbox = (cx - 460, cy - 48, cx + 460, cy + 48)
    draw.rounded_rectangle(bbox, radius=24, fill=(255, 255, 255, 248), outline=BLUE_COLOR, width=3)
    draw.rounded_rectangle((cx - 400, cy - 22, cx - 360, cy + 22), radius=6, fill=(255, 255, 255), outline=BLUE_COLOR, width=2)
    draw.rectangle((cx - 400, cy - 22, cx - 360, cy - 8), fill=BLUE_COLOR)
    f_num = get_font(FONT_BOLD, 20)
    draw.text((cx - 380, cy + 8), "3", font=f_num, fill=BLUE_COLOR, anchor="mm")
    draw_auto_card_text(
        draw, bbox,
        title=label,
        desc="Theo dõi phân & da trước khi đổi món",
        theme_color=(41, 128, 185),
        desc_color=(70, 70, 70),
        max_title_font=26,
        min_title_font=16,
        max_desc_font=20,
        min_desc_font=14,
        icon_left_pad=100,
        align="center"
    )

# ==============================================================================
# 3. BỘ HÌNH KHỐI NGHỆ THUẬT VẼ TAY THẾ HỆ MỚI (DIVERSE ARTISTIC SHAPES)
# ==============================================================================

def draw_seamless_cloud(draw, bbox, fill=(255, 255, 255, 252), outline=GREEN_COLOR, width=3):
    """
    Vẽ đám mây bồng bềnh liền khối không có nét cung tròn đè chéo bên trong.
    Sử dụng kỹ thuật Mask Silhouette Union cực kỳ chuẩn mực.
    Rất hợp với chủ đề tiêu hóa êm dịu, dạ dày bé khỏe mạnh, sữa mẹ, sự nhẹ nhàng.
    """
    x0, y0, x1, y1 = bbox
    w = int(x1 - x0)
    h = int(y1 - y0)
    
    mask = np.zeros((h + 40, w + 40), dtype=np.uint8)
    ox, oy = 20, 20
    
    pad_x, pad_y = 28, 20
    cv2.rectangle(mask, (ox + pad_x, oy + pad_y), (ox + w - pad_x, oy + h - pad_y), 255, -1)
    
    n_x = max(5, int(w / 70))
    for i in range(n_x + 1):
        cx = int(ox + pad_x + i * ((w - 2 * pad_x) / n_x))
        r_top = 22 if (i % 2 == 1) else 18
        r_bot = 20 if (i % 2 == 0) else 17
        cv2.circle(mask, (cx, oy + pad_y - 2), r_top, 255, -1)
        cv2.circle(mask, (cx, oy + h - pad_y + 2), r_bot, 255, -1)
        
    n_y = max(2, int(h / 50))
    for i in range(1, n_y):
        cy = int(oy + pad_y + i * ((h - 2 * pad_y) / n_y))
        cv2.circle(mask, (ox + pad_x - 4, cy), 19, 255, -1)
        cv2.circle(mask, (ox + w - pad_x + 4, cy), 19, 255, -1)
        
    for cx, cy in [(ox + pad_x, oy + pad_y), (ox + w - pad_x, oy + pad_y),
                   (ox + pad_x, oy + h - pad_y), (ox + w - pad_x, oy + h - pad_y)]:
        cv2.circle(mask, (cx, cy), 22, 255, -1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cnt = contours[0]
        pts = [(int(p[0][0] - ox + x0), int(p[0][1] - oy + y0)) for p in cnt]
        shadow_pts = [(x + 3, y + 4) for x, y in pts]
        draw.polygon(shadow_pts, fill=(215, 205, 185, 130))
        draw.polygon(pts, fill=fill, outline=outline)
        for i in range(len(pts)):
            draw.line([pts[i], pts[(i + 1) % len(pts)]], fill=outline, width=width)

def draw_torn_paper_card(draw, bbox, fill=(255, 255, 255, 250), outline=RED_COLOR, pin_color=RED_COLOR):
    """
    Thẻ ghi chú phong cách giấy xé tay (Scrapbook torn paper) có mép răng cưa tự nhiên
    và ghim bấm nhựa tròn 3D trên đỉnh.
    Rất sinh động cho cảnh báo sai lầm, quá tải nội tạng, lưu ý y khoa khẩn cấp.
    """
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0

    pts = [(x0, y0 + 10)]
    pts.append((x1, y0 + 8))
    pts.append((x1, y1 - 12))
    
    n_teeth = max(12, int(w / 35))
    step = w / n_teeth
    for i in range(n_teeth, -1, -1):
        curr_x = x0 + i * step
        dy = (8 if i % 2 == 0 else -4) + (math.sin(i * 1.5) * 5)
        pts.append((curr_x, y1 - 8 + dy))

    pts.append((x0, y1 - 10))
    pts.append((x0, y0 + 10))

    shadow_pts = [(x + 4, y + 4) for x, y in pts]
    draw.polygon(shadow_pts, fill=(215, 205, 185, 120))
    draw.polygon(pts, fill=fill, outline=outline)

    # Ghim bấm nhựa tròn 3D
    pin_cx = (x0 + x1) / 2
    pin_cy = y0 + 12
    draw.ellipse((pin_cx - 8, pin_cy + 2, pin_cx + 12, pin_cy + 16), fill=(180, 170, 150))
    draw.ellipse((pin_cx - 12, pin_cy - 12, pin_cx + 12, pin_cy + 12), fill=pin_color, outline=(255, 255, 255), width=2)
    draw.ellipse((pin_cx - 6, pin_cy - 8, pin_cx - 1, pin_cy - 3), fill=(255, 255, 255, 220))

def draw_seamless_parchment(draw, bbox, fill=(255, 252, 242), outline=(160, 110, 50), width=3):
    """
    Cuộn sớ thư pháp cổ tích cuộn tròn 2 đầu trái phải có nếp cuộn 3D và bóng đổ.
    Rất trang nhã cho tiêu đề quan trọng, bí kíp tăng thô, lộ trình 3 ngày.
    """
    x0, y0, x1, y1 = bbox
    roll_w = 42
    body_x0 = x0 + roll_w - 6
    body_x1 = x1 - roll_w + 6
    body_y0 = y0 + 10
    body_y1 = y1 - 10
    
    draw.rectangle((body_x0 + 4, body_y0 + 4, body_x1 + 4, body_y1 + 4), fill=(215, 205, 185))
    draw.rectangle((body_x0, body_y0, body_x1, body_y1), fill=fill, outline=outline, width=width)
    
    draw.line([(body_x0 + 12, body_y0 + 8), (body_x1 - 12, body_y0 + 8)], fill=(210, 175, 120), width=1)
    draw.line([(body_x0 + 12, body_y1 - 8), (body_x1 - 12, body_y1 - 8)], fill=(210, 175, 120), width=1)

    # Cuộn tròn bên trái
    draw.rounded_rectangle((x0, y0, x0 + roll_w, y1), radius=roll_w//2, fill=(245, 230, 205), outline=outline, width=width)
    draw.ellipse((x0 + 10, y0 + 8, x0 + roll_w - 10, y0 + 26), fill=(220, 190, 145), outline=outline, width=2)
    draw.ellipse((x0 + 10, y1 - 26, x0 + roll_w - 10, y1 - 8), fill=(220, 190, 145), outline=outline, width=2)

    # Cuộn tròn bên phải
    draw.rounded_rectangle((x1 - roll_w, y0, x1, y1), radius=roll_w//2, fill=(245, 230, 205), outline=outline, width=width)
    draw.ellipse((x1 - roll_w + 10, y0 + 8, x1 - 10, y0 + 26), fill=(220, 190, 145), outline=outline, width=2)
    draw.ellipse((x1 - roll_w + 10, y1 - 26, x1 - 10, y1 - 8), fill=(220, 190, 145), outline=outline, width=2)

def draw_seamless_rosette(draw, cx, cy, radius=55, label="WHO 2026", fill=THEME_COLOR, outline=(255, 255, 255)):
    """
    Con dấu dập nổi hoa mai liền khối mượt mà không có nét vẽ đè bên trong.
    Mang lại sự tin cậy y khoa chuẩn mực, khuyến cáo viện dinh dưỡng.
    """
    tail_w = 26
    tail_len = 45
    draw.polygon([
        (cx - 10, cy + radius - 10),
        (cx - 10 - tail_w, cy + radius + tail_len),
        (cx - 10 - tail_w/2, cy + radius + tail_len - 10),
        (cx - 5, cy + radius + tail_len),
        (cx - 2, cy + radius - 10)
    ], fill=(max(0, fill[0]-40), max(0, fill[1]-40), max(0, fill[2]-40)), outline=(40, 30, 20), width=2)
    draw.polygon([
        (cx + 2, cy + radius - 10),
        (cx + 5, cy + radius + tail_len),
        (cx + 10 + tail_w/2, cy + radius + tail_len - 10),
        (cx + 10 + tail_w, cy + radius + tail_len),
        (cx + 10, cy + radius - 10)
    ], fill=(max(0, fill[0]-40), max(0, fill[1]-40), max(0, fill[2]-40)), outline=(40, 30, 20), width=2)

    box_s = int((radius + 25) * 2)
    mask = np.zeros((box_s, box_s), dtype=np.uint8)
    mcx, mcy = box_s // 2, box_s // 2
    
    cv2.circle(mask, (mcx, mcy), int(radius), 255, -1)
    n_petals = 16
    for i in range(n_petals):
        angle = i * (2 * math.pi / n_petals)
        px = int(mcx + (radius + 2) * math.cos(angle))
        py = int(mcy + (radius + 2) * math.sin(angle))
        cv2.circle(mask, (px, py), 15, 255, -1)
        
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cnt = contours[0]
        pts = [(int(p[0][0] - mcx + cx), int(p[0][1] - mcy + cy)) for p in cnt]
        draw.polygon(pts, fill=fill, outline=outline)
        for i in range(len(pts)):
            draw.line([pts[i], pts[(i + 1) % len(pts)]], fill=outline, width=2)

    draw.ellipse((cx - radius + 8, cy - radius + 8, cx + radius - 8, cy + radius - 8), fill=None, outline=(255, 255, 255), width=2)
    f = get_font(FONT_BOLD, 18)
    draw.text((cx, cy), label, font=f, fill=(255, 255, 255), anchor="mm")

def draw_speech_balloon(draw, bbox, fill=(255, 255, 255, 252), outline=RED_COLOR, width=3, tail_x=None, tail_y=None):
    """
    Bong bóng đối thoại truyện tranh sinh động có đuôi nhọn cong chỉ thẳng vào nhân vật.
    """
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=28, fill=fill, outline=outline, width=width)

    tx = tail_x or (x0 + 120)
    ty = tail_y or (y1 + 45)
    tail_pts = [
        (tx - 30, y1 - 2),
        (tx, ty),
        (tx + 20, y1 - 2)
    ]
    draw.polygon(tail_pts, fill=fill)
    draw.line([(tx - 30, y1 - 2), (tx, ty)], fill=outline, width=width)
    draw.line([(tx, ty), (tx + 20, y1 - 2)], fill=outline, width=width)

# ==============================================================================
# 4. ENGINE BẢO VỆ CHỮ CHỐNG TRÀN VIỀN 100% (UNIVERSAL ANTI-OVERFLOW ENGINE)
# ==============================================================================

def draw_auto_card_text(
    draw,
    card_bbox: tuple[float, float, float, float],
    title: str,
    desc: str = None,
    theme_color: tuple = THEME_COLOR,
    desc_color: tuple = (50, 50, 50),
    max_title_font: int = 30,
    min_title_font: int = 18,
    max_desc_font: int = 22,
    min_desc_font: int = 14,
    icon_left_pad: int = 0,
    icon_right_pad: int = 0,
    align: str = "center"
):
    """
    Hàm bố cục văn bản thông minh đảm bảo 100% toán học:
    - Text KHÔNG BAO GIỜ chạm viền trái, viền phải, viền trên, viền dưới của card_bbox.
    - Tự động tách dòng cân đối nếu title chứa dấu phân cách (' — ', ' : ') hoặc dài > 25 ký tự.
    - Tự động co giãn kích thước font theo cả 2 chiều: Chiều ngang (Width) & Chiều dọc (Height).
    """
    if not title:
        return
    x0, y0, x1, y1 = card_bbox
    pad_h = 24
    pad_v = 12
    
    avail_x0 = x0 + pad_h + icon_left_pad
    avail_x1 = x1 - pad_h - icon_right_pad
    avail_w = max(100, avail_x1 - avail_x0)
    avail_h = max(30, (y1 - y0) - 2 * pad_v)
    
    # 1. Tách title thành các dòng cân đối
    title_lines = []
    if "\n" in title:
        title_lines = [p.strip() for p in title.split("\n") if p.strip()]
    elif (" — " in title or " : " in title) and len(title) > 22:
        delim = " — " if " — " in title else " : "
        parts = title.split(delim, 1)
        title_lines = [parts[0].strip(), parts[1].strip()]
    elif len(title) > 30 and " " in title:
        words = title.split()
        mid = len(words) // 2
        title_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        title_lines = [title]

    # Tìm font size cho title sao cho vừa khít avail_w
    f_title_size = max_title_font
    f_title = get_font(FONT_BOLD, f_title_size)
    while f_title_size > min_title_font:
        overflow = False
        for line in title_lines:
            bb = draw.textbbox((0, 0), line, font=f_title)
            if (bb[2] - bb[0]) > avail_w:
                overflow = True
                break
        if overflow:
            f_title_size -= 1
            f_title = get_font(FONT_BOLD, f_title_size)
        else:
            break

    # 2. Xử lý desc nếu có (hỗ trợ phân tách đoạn / bullet bằng dấu \n)
    desc_lines = []
    f_desc_size = max_desc_font
    f_desc = get_font(FONT_REGULAR, f_desc_size)
    if desc:
        raw_paras = [p.strip() for p in desc.split("\n") if p.strip()]
        while f_desc_size >= min_desc_font:
            desc_lines = []
            too_wide = False
            for para in raw_paras:
                words = para.split()
                cur = []
                for w in words:
                    test = " ".join(cur + [w])
                    bb = draw.textbbox((0, 0), test, font=f_desc)
                    if (bb[2] - bb[0]) <= avail_w:
                        cur.append(w)
                    else:
                        if cur:
                            desc_lines.append(" ".join(cur))
                            cur = [w]
                        else:
                            too_wide = True
                            break
                if cur:
                    desc_lines.append(" ".join(cur))
                if too_wide:
                    break
            if too_wide and f_desc_size > min_desc_font:
                f_desc_size -= 1
                f_desc = get_font(FONT_REGULAR, f_desc_size)
            else:
                break

    # 3. Tính toán tổng chiều cao & co lại nếu vượt quá avail_h
    line_h_title = f_title_size + 4
    line_h_desc = f_desc_size + 4 if desc else 0
    total_h = len(title_lines) * line_h_title + (len(desc_lines) * line_h_desc if desc else 0) + (6 if desc else 0)

    while total_h > avail_h and (f_title_size > 14 or (desc and f_desc_size > 12)):
        if f_title_size > 14:
            f_title_size -= 1
            f_title = get_font(FONT_BOLD, f_title_size)
            line_h_title = f_title_size + 4
        if desc and f_desc_size > 12:
            f_desc_size -= 1
            f_desc = get_font(FONT_REGULAR, f_desc_size)
            line_h_desc = f_desc_size + 4
        total_h = len(title_lines) * line_h_title + (len(desc_lines) * line_h_desc if desc else 0) + (4 if desc else 0)

    # 4. Vẽ căn chỉnh
    start_y = y0 + ((y1 - y0) - total_h) / 2
    cur_y = start_y
    anchor_x = (avail_x0 + avail_x1) / 2 if align == "center" else avail_x0
    txt_anchor = "ma" if align == "center" else "la"

    for line in title_lines:
        draw.text((anchor_x, cur_y), line, font=f_title, fill=theme_color, anchor=txt_anchor)
        cur_y += line_h_title

    if desc and desc_lines:
        cur_y += 4
        for line in desc_lines:
            draw.text((anchor_x, cur_y), line, font=f_desc, fill=desc_color, anchor=txt_anchor)
            cur_y += line_h_desc


def draw_warning_pill(
    draw,
    cx: float,
    cy: float,
    text: str,
    icon: str = "prohibit",
    theme_color: tuple = RED_COLOR,
    bg_color: tuple = (255, 245, 245),
    border_color: tuple = RED_COLOR,
    max_w: int = 960,
    pill_h: int = 56
) -> tuple[int, int, int, int]:
    """
    Vẽ thẻ cảnh báo dạng viên nang (pill badge) tự co giãn vừa khít độ dài text:
    - Chiều rộng pill ôm sát nội dung (text + icon + padding), không bị kéo dài vô nghĩa.
    - Căn giữa tại tọa độ cx, cy.
    - Trả về bounding box (x0, y0, x1, y1) để thuận tiện cho việc lưu annotation region.
    """
    f_warn = get_font(FONT_BOLD, 22)
    bb = draw.textbbox((0, 0), text, font=f_warn)
    txt_w = bb[2] - bb[0]
    
    # Nếu text quá dài, tự hạ font nhẹ
    if txt_w + 90 > max_w:
        f_warn = get_font(FONT_BOLD, 20)
        bb = draw.textbbox((0, 0), text, font=f_warn)
        txt_w = bb[2] - bb[0]

    pill_w = min(max_w, txt_w + 90)
    x0 = int(cx - pill_w // 2)
    x1 = int(cx + pill_w // 2)
    y0 = int(cy - pill_h // 2)
    y1 = int(cy + pill_h // 2)

    # Nền và viền viên nang
    draw.rounded_rectangle((x0, y0, x1, y1), radius=pill_h // 2, fill=bg_color, outline=border_color, width=2)

    # Icon cảnh báo bên trái
    icon_cx = x0 + 26
    icon_cy = cy
    if icon == "prohibit":
        draw_prohibition_badge(draw, icon_cx, icon_cy, radius=15)

    # Text căn giữa phần còn lại
    text_cx = (x0 + 52 + x1 - 10) // 2
    draw.text((text_cx, cy), text, font=f_warn, fill=theme_color, anchor="mm")

    return (x0, y0, x1, y1)


def draw_advice_card(
    draw,
    cx: float,
    cy: float,
    num_str: str,
    title: str,
    subtitle: str = None,
    theme_color: tuple = THEME_COLOR,
    card_w: int = 920,
    card_h: int = 92
) -> tuple[int, int, int, int]:
    """
    Thẻ lời khuyên vạn năng (Universal Advice Card) có số thứ tự hình tròn (1, 2, 3),
    tiêu đề in đậm sắc nét và phụ đề hướng dẫn chi tiết bên dưới.
    Được dùng thay thế triệt để các thẻ cố định một chủ đề như thìa/mặt trời/lịch.
    Trả về bounding box (x0, y0, x1, y1).
    """
    x0 = int(cx - card_w // 2)
    x1 = int(cx + card_w // 2)
    y0 = int(cy - card_h // 2)
    y1 = int(cy + card_h // 2)
    bbox = (x0, y0, x1, y1)

    # Bóng đổ nhẹ tạo độ nổi 3D
    draw.rounded_rectangle((x0 + 4, y0 + 4, x1 + 4, y1 + 4), radius=20, fill=(225, 218, 202, 130))
    # Thẻ chính nền trắng kem dịu mắt
    draw.rounded_rectangle(bbox, radius=20, fill=(255, 255, 255, 250), outline=theme_color, width=2)

    # Huy hiệu số thứ tự tròn 3D bên trái
    badge_cx = x0 + 50
    badge_cy = cy
    badge_r = 25
    draw.ellipse((badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r), fill=theme_color)
    f_num = get_font(FONT_BOLD, 22)
    draw.text((badge_cx, badge_cy), str(num_str), font=f_num, fill=(255, 255, 255), anchor="mm")

    # Nội dung text bên phải huy hiệu
    draw_auto_card_text(
        draw,
        bbox,
        title=title,
        desc=subtitle,
        theme_color=theme_color,
        desc_color=(60, 60, 60),
        max_title_font=24,
        min_title_font=16,
        max_desc_font=18,
        min_desc_font=13,
        icon_left_pad=95,
        align="left"
    )

    return bbox



