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
from whiteboard_app.voice import generate_scene_voices
from whiteboard_app.timeline import compile_scene_timeline
from whiteboard_app.renderer import build_commands, subprocess_environment

CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")
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
    draw_rounded_rect(draw, (100, 260, 980, 360), radius=20, fill=theme_color)
    f_badge = get_font(FONT_BOLD, 44)
    draw.text((540, 310), badge_text, font=f_badge, fill=(255, 255, 255), anchor="mm")

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
        draw_rounded_rect(draw, (80, cur_y + 30, 170, cur_y + 120), radius=16, fill=theme_color)
        f_num = get_font(FONT_BOLD, 46)
        draw.text((125, cur_y + 75), f"0{i+1}", font=f_num, fill=(255, 255, 255), anchor="mm")
        
        parts = pt.split(":", 1)
        if len(parts) == 2:
            title_text = parts[0].strip()
            body_text = parts[1].strip()
        else:
            title_text = f"Bước {i+1}"
            body_text = pt.strip()

        draw.text((200, cur_y + 60), title_text.upper(), font=f_bullet_title, fill=theme_color, anchor="lm")
        
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

# Kịch bản 4 Cảnh chi tiết cho toàn bộ các Slot từ Slot 2 đến Slot 11
SCENES_CONFIG = {
    2: {
        "title": "Gạo Tẻ Nấu Cháo Rây Bé Mấy Tháng Ăn Được?",
        "color": (230, 126, 34),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Rất nhiều mẹ hỏi Mẹ Dâu: Bé tròn sáu tháng thì nấu cháo rây bằng gạo gì là an toàn nhất? Có nên trộn gạo nếp, hạt sen hay đậu xanh cho con bổ béo không? Câu trả lời dứt khoát là: Tuyệt đối không mẹ nhé!",
                "banner": "CHỌN GẠO GÌ NẤU CHÁO RÂY CHO BÉ 6 THÁNG?",
                "badge": "⚠️ CẢNH BÁO NHẦM LẪN NGÀY 1",
                "bullets": [
                    "Câu hỏi phổ biến: Có nên trộn gạo nếp, hạt sen, đậu xanh?",
                    "Thói quen sai lầm: Nghĩ trộn nhiều hạt sẽ giúp con tăng cân",
                    "Khuyến cáo y khoa: Tuyệt đối không trộn hạt giai đoạn đầu"
                ],
                "cta": "Cùng Mẹ Dâu tìm hiểu cơ chế tiêu hóa của con nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Hệ tiêu hóa của bé sáu tháng men amylase còn rất ít, chỉ vừa đủ để phân giải tinh bột thuần từ gạo tẻ trắng. Nếu mẹ trộn gạo nếp dẻo quánh hay hạt sen nhiều tinh bột kháng, dạ dày con sẽ bị quá tải, gây đầy hơi, chướng bụng và khó tiêu kéo dài.",
                "banner": "TẠI SAO BÉ CHƯA THỂ ĂN GẠO NẾP & HẠT SEN?",
                "badge": "🔬 GIẢI MÃ CƠ CHẾ TIÊU HÓA",
                "bullets": [
                    "Men tiêu hóa Amylase: Còn rất ít, chỉ tiêu hóa được tinh bột đơn",
                    "Gạo nếp & Hạt sen: Quá dẻo quánh gây ứ đọng dạ dày bé",
                    "Hậu quả cho bé: Đầy hơi, chướng bụng, táo bón và nôn trớ sợ ăn"
                ],
                "cta": "Chỉ chọn nguyên liệu thuần khiết nhất cho con mẹ nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Cách chuẩn nhất cho con là: Mẹ dùng gạo tẻ thơm nguyên cám, nấu theo tỷ lệ một gạo mười nước. Nấu chín nhừ rồi rây qua lưới hai lần khi còn nóng ấm để đạt độ sánh mịn màng như sữa mẹ.",
                "banner": "CÔNG THỨC CHÁO RÂY 1:10 CHUẨN Y KHOA",
                "badge": "🥣 CÔNG THỨC 3 BƯỚC NẤU CHUẨN",
                "bullets": [
                    "Bước 1: Dùng gạo tẻ thơm nguyên cám, vo nhẹ giữ vitamin B",
                    "Bước 2: Nấu chuẩn tỷ lệ 1 gạo 10 nước lửa nhỏ cho nhừ tơi",
                    "Bước 3: Rây qua lưới 2 lần khi ấm để đạt độ mịn như sữa"
                ],
                "cta": "Cháo mịn màng giúp con nuốt êm không nghẹn!"
            },
            {
                "id": "scene_04",
                "voice": "Mẹ chỉ cần cho con nếm một đến hai thìa nhỏ ngày đầu tiên thôi nhé. Mẹ còn phân vân nguyên liệu nào nữa không? Hãy để lại bình luận và bấm Follow kênh Ăn dặm mẹ Dâu để cùng mẹ chăm con chuẩn y khoa nhé!",
                "banner": "NGUYÊN TẮC VÀNG NGÀY ĐẦU TIÊN",
                "badge": "🌟 LỜI KHUYÊN TỪ MẸ DÂU",
                "bullets": [
                    "Liều lượng khởi đầu: Chỉ 1 đến 2 thìa nhỏ làm quen vị giác",
                    "Không nêm gia vị: Giữ trọn vị ngọt tự nhiên của hạt gạo",
                    "Theo dõi tiêu hóa: Quan sát phân và phản ứng trong 3 ngày"
                ],
                "cta": "👉 Bấm Follow kênh để xem thực đơn ngày tiếp theo nhé!"
            }
        ]
    },
    3: {
        "title": "Mẹo Tăng Độ Thô Không Nôn Trớ Ngày 1",
        "color": (46, 204, 113),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Cứ mỗi lần cho con ăn thức ăn lợn cợn là con lại ọe khan, nôn trớ đỏ cả mặt khiến mẹ xót ruột không dám tăng thô nữa. Nhưng mẹ ơi, phản xạ ọe không phải là hóc nghẹn, mà là cơ chế tự bảo vệ tự nhiên của cơ thể con đấy!",
                "banner": "CON ỌE KHAN KHI TĂNG THÔ: ĐỪNG SỢ MẸ ƠI!",
                "badge": "⚠️ HIỂU ĐÚNG PHẢN XẠ ỌE CỦA BÉ",
                "bullets": [
                    "Nỗi sợ phổ biến: Thấy con ọe khan là dừng tăng thô ngay",
                    "Sự thật y khoa: Ọe là cơ chế bảo vệ đẩy thức ăn to ra ngoài",
                    "Hậu quả ăn mịn quá lâu: Bé lười nhai, kén ăn và chậm nói"
                ],
                "cta": "Cùng Mẹ Dâu tìm hiểu cơ chế lưỡi của con nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Ở bé sáu tháng, điểm kích hoạt phản xạ ọe nằm ngay giữa lưỡi chứ không phải ở đáy họng như người lớn. Nhờ phản xạ này, con học cách dùng lưỡi đẩy thức ăn to ra ngoài an toàn. Nếu mẹ sợ mà cứ cho ăn bột mịn mãi, sau chín tháng con sẽ lười nhai và biếng ăn kéo dài.",
                "banner": "VÙNG NHẠY CẢM TRÊN LƯỠI BÉ 6 THÁNG",
                "badge": "🔬 CƠ CHẾ PHẢN XẠ LƯỠI TỰ NHIÊN",
                "bullets": [
                    "Điểm nhạy cảm ọe: Nằm ở giữa lưỡi, kích hoạt cực sớm",
                    "Chức năng bảo vệ: Giúp con học dùng lưỡi di chuyển thức ăn",
                    "Giai đoạn vàng: 6 đến 9 tháng là lúc tập cơ hàm tốt nhất"
                ],
                "cta": "Mẹ hãy kiên nhẫn để con học kỹ năng nhai nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Bí quyết tăng thô êm ái cho mẹ gồm ba bước: Bước một, hạ tỷ lệ nước từ từ, từ cháo loãng một mười sang cháo vỡ một bảy. Bước hai, dùng thìa phẳng đặt nhẹ đầu lưỡi, kiên nhẫn đợi con tự ngậm môi kéo thức ăn vào. Bước ba, bổ sung rau củ hấp mềm dạng que để con tập gặm bằng nướu.",
                "banner": "KỸ THUẬT TẬP CƠ HÀM 3 BƯỚC KHÔNG NÔN TRỚ",
                "badge": "🥦 3 BƯỚC TĂNG THÔ AN TOÀN",
                "bullets": [
                    "Bước 1: Giảm nước từ từ, chuyển cháo rây 1:10 sang vỡ 1:7",
                    "Bước 2: Đặt thìa phẳng đầu lưỡi, để con tự ngậm môi kéo vào",
                    "Bước 3: Cho con gặm rau củ hấp mềm dạng que an toàn"
                ],
                "cta": "Con sẽ học nhai nuốt thuần thục từng ngày!"
            },
            {
                "id": "scene_04",
                "voice": "Hãy bình tĩnh đồng hành và khen ngợi mỗi khi con nuốt thành công một thìa thức ăn thô mẹ nhé. Bấm Follow kênh Ăn dặm mẹ Dâu để nhận trọn bộ cẩm nang xử lý nôn trớ cho con!",
                "banner": "LỜI KHUYÊN ĐỒNG HÀNH TỪ MẸ DÂU",
                "badge": "🌟 TÂM LÝ BÌNH TĨNH CỦA MẸ",
                "bullets": [
                    "Không la mắng hốt hoảng: Giữ không khí bàn ăn vui vẻ",
                    "Khen ngợi động viên: Khích lệ mỗi khi con nuốt thành công",
                    "Đồng hành kiên trì: Giới thiệu món mới từ 5 đến 7 lần"
                ],
                "cta": "👉 Bấm Follow kênh để xem thêm mẹo ăn dặm mỗi ngày!"
            }
        ]
    },
    4: {
        "title": "Giải Mã Lầm Tưởng Y Khoa #1",
        "color": (217, 83, 79),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Ninh xương lấy nước nấu cháo cho ngọt nước bổ xương, hay nêm chút nước mắm cho con ăn đậm đà bắt miệng? Những thói quen truyền miệng quen thuộc này thực ra đang âm thầm làm hại sức khỏe của con đấy mẹ ơi!",
                "banner": "3 LẦM TƯỞNG ĂN DẶM HẠI THẬN BÉ NGUY HIỂM",
                "badge": "🚨 CẢNH BÁO QUAN NIỆM TRUYỀN MIỆNG",
                "bullets": [
                    "Ninh nước hầm xương: Nghĩ nước ngọt hầm xương sẽ bổ canxi",
                    "Nêm mắm muối sớm: Muốn con ăn đậm đà để nhanh tăng cân",
                    "Nguy cơ tiềm ẩn: Tổn thương thận và rối loạn chuyển hóa"
                ],
                "cta": "Cùng xem bằng chứng khoa học từ Viện Dinh Dưỡng nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Sự thật y khoa đã chứng minh: Nước hầm xương chỉ toàn chất béo no khó tiêu và tủy xương chứa rất ít canxi. Còn muối và nước mắm sẽ phá hủy thận non nớt của bé dưới một tuổi, làm tăng nguy cơ cao huyết áp và tổn thương vi chất sau này.",
                "banner": "SỰ THẬT Y KHOA VỀ NƯỚC HẦM XƯƠNG & GIA VỊ",
                "badge": "🔬 BẰNG CHỨNG Y HỌC CHỨNG MINH",
                "bullets": [
                    "Nước hầm xương: Chỉ toàn mỡ no khó tiêu, canxi không tan",
                    "Muối và nước mắm: Bắt thận non nớt làm việc quá tải gấp 5 lần",
                    "Hệ quả lâu dài: Tăng nguy cơ tim mạch và biếng ăn sau này"
                ],
                "cta": "Nuôi con bằng tri thức chuẩn mực mẹ nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Mẹ hãy nhớ kỹ ba nguyên tắc bất biến: Thứ nhất, tuyệt đối không nêm bất kỳ loại gia vị nào dưới một tuổi. Thứ hai, cho con ăn cả xác thịt cá xay nhuyễn thay vì chỉ lấy nước ngọt. Thứ ba, tuyệt đối không rơ lưỡi cho con bằng mật ong vì nguy cơ ngộ độc bào tử vi khuẩn.",
                "banner": "3 NGUYÊN TẮC Y KHOA BẤT BIẾN KHI BẮT ĐẦU",
                "badge": "📋 3 NGUYÊN TẮC VÀNG BẢO VỆ CON",
                "bullets": [
                    "Nguyên tắc 1: Không nêm bất kỳ gia vị nào dưới 1 tuổi",
                    "Nguyên tắc 2: Ăn cả phần cái xay nhuyễn, không chỉ lấy nước",
                    "Nguyên tắc 3: Tuyệt đối không dùng mật ong rơ lưỡi bé"
                ],
                "cta": "Mẹ hãy ghi nhớ kỹ để bảo vệ con yêu nhé!"
            },
            {
                "id": "scene_04",
                "voice": "Nuôi con bằng tri thức khoa học và sự thấu hiểu là món quà lớn nhất mẹ dành cho con. Hãy bấm Follow kênh Ăn dặm mẹ Dâu để cùng mẹ bảo vệ con yêu bằng kiến thức chuẩn y khoa nhé!",
                "banner": "NUÔI CON BẰNG TRI THỨC VÀ TÌNH YÊU",
                "badge": "💖 THÔNG ĐIỆP TỪ ĂN DẶM MẸ DÂU",
                "bullets": [
                    "Tri thức khoa học: Nền tảng vững chắc cho con phát triển",
                    "Bản lĩnh người mẹ: Vững vàng trước những lời truyền miệng",
                    "Đồng hành thông thái: Cho con một khởi đầu hoàn hảo nhất"
                ],
                "cta": "👉 Bấm Follow kênh để xem thêm bài học y khoa chuẩn nhé!"
            }
        ]
    },
    5: {
        "title": "Món Bánh Ăn Dặm Chiều Ngày 1",
        "color": (243, 156, 18),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Bữa phụ chiều bốn giờ con đói bụng mà mẹ chưa biết làm món gì vừa nhanh vừa bổ dưỡng? Thử ngay món bánh pancake yến mạch chuối tiêu áp chảo thơm lừng, làm chưa đầy mười phút và không cần lò nướng nhé!",
                "banner": "BÁNH PANCAKE YẾN MẠCH CHUỐI TIÊU SIÊU NHANH",
                "badge": "🥞 BỮA PHỤ 10 PHÚT KHÔNG CẦN LÒ",
                "bullets": [
                    "Bữa phụ chiều lý tưởng: Bổ sung năng lượng sau giấc ngủ",
                    "Không cần lò nướng: Chỉ cần chảo chống dính quen thuộc",
                    "Tiết kiệm thời gian: Làm trong 10 phút, mẹ nhàn tênh"
                ],
                "cta": "Xem ngay nguyên liệu đơn giản trong căn bếp mẹ nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Chuối tiêu chín tự nhiên cung cấp vị ngọt dịu kích thích vị giác, kết hợp yến mạch giàu chất xơ hòa tan giúp đường ruột bé tiêu hóa cực kỳ êm ái, phòng ngừa táo bón hiệu quả cho các bé mới bắt đầu ăn dặm.",
                "banner": "GIÀU CHẤT XƠ HÒA TAN — TIÊU HÓA ÊM ÁI",
                "badge": "🍌 DINH DƯỠNG VÀNG CHO BÉ KHỞI ĐẦU",
                "bullets": [
                    "Chuối tiêu chín: Vị ngọt dịu tự nhiên, kích thích vị giác",
                    "Yến mạch nguyên chất: Giàu chất xơ hòa tan beta-glucan",
                    "Chống táo bón: Nhuận tràng, làm mềm phân cực tốt"
                ],
                "cta": "Món bánh vừa ngon vừa bổ cho hệ tiêu hóa của con!"
            },
            {
                "id": "scene_03",
                "voice": "Công thức siêu đơn giản: Bước một, mẹ nghiền nhuyễn nửa quả chuối tiêu chín. Bước hai, trộn cùng hai thìa bột yến mạch và một lòng đỏ trứng gà ta đã hấp sơ. Bước ba, múc từng thìa nhỏ áp chảo chống dính lửa liu riu hai phút mỗi mặt cho vàng ruộm.",
                "banner": "CÔNG THỨC 3 BƯỚC ÁP CHẢO SIÊU DỄ LÀM",
                "badge": "🥣 3 BƯỚC CHẾ BIẾN CHI TIẾT",
                "bullets": [
                    "Bước 1: Nghiền nhuyễn nửa quả chuối chín thơm",
                    "Bước 2: Trộn 2 thìa bột yến mạch và 1 lòng đỏ trứng gà",
                    "Bước 3: Áp chảo lửa nhỏ 2 phút mỗi mặt cho vàng ruộm"
                ],
                "cta": "Bánh thơm nức mũi cả gian bếp của mẹ!"
            },
            {
                "id": "scene_04",
                "voice": "Chiếc bánh mềm xốp, thơm nức mũi sẽ khiến bé cầm ăn hào hứng vô cùng. Mẹ hãy lưu lại công thức ngay và bấm Follow kênh Ăn dặm mẹ Dâu để học thêm nhiều món bánh ngon mỗi ngày nhé!",
                "banner": "BÉ CẦM GẶM HÀO HỨNG & TẬP NHAI",
                "badge": "🌟 KỸ NĂNG CẦM NẮM TỰ CHỈ HUY",
                "bullets": [
                    "Cấu trúc mềm xốp: Dễ tan trong miệng, không lo hóc nghẹn",
                    "Rèn luyện kỹ năng: Giúp bé phối hợp tay mắt và tập cầm nắm",
                    "Bảo quản tiện lợi: Dùng trong ngày hoặc cất hộp kín"
                ],
                "cta": "👉 Bấm Follow kênh để xem thực đơn món bánh tiếp theo nhé!"
            }
        ]
    },
    6: {
        "title": "Cấp Cứu Tiêu Hóa Cho Bé #1",
        "color": (26, 188, 156),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Vừa cho con ăn dặm được một hai ngày mà con đã đi ngoài phân sống, rặn đỏ bừng mặt hay hai ba ngày chưa đi vệ sinh? Mẹ đừng quá hoảng sợ mà vội vàng thụt tháo cho con nhé!",
                "banner": "BÉ MỚI ĂN DẶM BỊ TÁO BÓN: ĐỪNG VỘI THỤT THÁO!",
                "badge": "🩺 CẤP CỨU TIÊU HÓA NGÀY ĐẦU",
                "bullets": [
                    "Triệu chứng thường gặp: Rặn đỏ mặt, phân sống, táo bón",
                    "Sai lầm nguy hiểm: Vội vàng thụt tháo làm giãn cơ vòng hậu môn",
                    "Lời khuyên bác sĩ: Bình tĩnh tìm hiểu nguyên nhân sinh lý"
                ],
                "cta": "Xem ngay cơ chế thích nghi đường ruột của con nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Khi chuyển từ sữa lỏng sang thức ăn dặm, hệ vi sinh đường ruột của con cần từ ba đến năm ngày để làm quen với chất xơ và tinh bột mới. Nếu mẹ đổi món quá dồn dập hoặc cho ăn quá nhiều chất xơ thô, ruột con sẽ lập tức bị co thắt.",
                "banner": "CƠ CHẾ THÍCH NGHI CỦA HỆ VI SINH ĐƯỜNG RUỘT",
                "badge": "🔬 CƠ CHẾ SINH LÝ ĐƯỜNG RUỘT",
                "bullets": [
                    "Thời gian thích nghi: Cần 3 đến 5 ngày cho men vi sinh làm quen",
                    "Nguyên nhân co thắt: Đổi món quá dồn dập, thức ăn quá đặc",
                    "Lưu ý quan trọng: Không ép ăn dặm khi con đang khó chịu"
                ],
                "cta": "Áp dụng ngay 3 bước cấp cứu êm ái tại nhà mẹ nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Mẹ hãy cấp cứu êm ái cho con bằng ba bước chuẩn y khoa: Bước một, bổ sung ngay chất xơ hòa tan từ mồng tơi hoặc khoai lang nghiền. Bước hai, massage bụng nhẹ nhàng theo chiều kim đồng hồ quanh rốn mỗi ngày hai lần. Bước ba, duy trì đủ lượng sữa và bổ sung men vi sinh chuyên biệt.",
                "banner": "QUY TRÌNH 3 BƯỚC XỬ LÝ ÊM ÁI CHUẨN Y KHOA",
                "badge": "🌿 3 BƯỚC PHỤC HỒI TIÊU HÓA",
                "bullets": [
                    "Bước 1: Bổ sung chất xơ hòa tan từ khoai lang, mồng tơi",
                    "Bước 2: Massage bụng theo chiều kim đồng hồ 5 phút quanh rốn",
                    "Bước 3: Duy trì đủ lượng sữa và men vi sinh lợi khuẩn"
                ],
                "cta": "Hệ tiêu hóa con sẽ êm ái trở lại ngay!"
            },
            {
                "id": "scene_04",
                "voice": "Nếu con quấy khóc bỏ bú kèm sốt, mẹ cần đưa con đến bác sĩ chuyên khoa ngay nhé. Bấm Follow kênh Ăn dặm mẹ Dâu để nhận hướng dẫn chăm sóc tiêu hóa an toàn cho bé!",
                "banner": "DẤU HIỆU CẢNH BÁO CẦN ĐI BÁC SĨ",
                "badge": "⚠️ KHI NÀO CẦN ĐI VIỆN?",
                "bullets": [
                    "Dấu hiệu nguy hiểm: Con sốt, nôn trớ liên tục, phân có nhầy máu",
                    "Bỏ bú mệt lả: Cần đưa đến cơ sở y tế gần nhất khám ngay",
                    "Đồng hành an tâm: Luôn theo dõi phân hàng ngày của bé"
                ],
                "cta": "👉 Bấm Follow kênh để cập nhật cẩm nang tiêu hóa cho bé!"
            }
        ]
    },
    7: {
        "title": "Món Cháo Tối Ấm Bụng Ngày 1",
        "color": (52, 152, 219),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Mẹ có biết: Một bữa tối ấm bụng, nấu đúng nguyên liệu dễ tiêu sẽ giúp con no lâu, ngủ một mạch xuyên đêm mà không bị lục đục giật mình thức giấc đòi bú không?",
                "banner": "CHÁO TỐI ẤM BỤNG GIÚP BÉ NGỦ XUYÊN ĐÊM",
                "badge": "🌙 CHĂM SÓC GIẤC NGỦ BÉ YÊU",
                "bullets": [
                    "Nỗi ám ảnh thức đêm: Con trằn trọc đòi bú, mẹ mất ngủ kiệt sức",
                    "Bí quyết từ bữa tối: Tiêu hóa êm ái tạo nền tảng ngủ sâu",
                    "Nguyên tắc vàng: Nhẹ bụng, no lâu, không gây đầy hơi"
                ],
                "cta": "Cùng tìm hiểu sai lầm ăn tối nhiều mẹ mắc phải nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Nhiều mẹ nghĩ cho con ăn thật no với nhiều thịt cá vào buổi tối để con ngủ sâu giấc. Nhưng đây lại là sai lầm khiến dạ dày bé phải làm việc cật lực suốt đêm, gây trào ngược, đầy bụng và khó ngủ trằn trọc.",
                "banner": "SAI LẦM KHI CHO BÉ ĂN ĐẠM NẶNG BUỔI TỐI",
                "badge": "⚠️ ĐỪNG CHO ĂN ĐẠM NẶNG BUỔI TỐI",
                "bullets": [
                    "Thói quen sai lầm: Nấu nhiều thịt cá, hải sản vào bữa tối",
                    "Gánh nặng dạ dày: Hệ tiêu hóa phải cày ải suốt đêm dài",
                    "Hậu quả cho con: Trào ngược, ợ hơi, khó ngủ và quấy khóc"
                ],
                "cta": "Xem ngay công thức cháo hạt sen bí đỏ êm ái nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Bữa tối hoàn hảo cho bé mới ăn dặm là: Súp bí đỏ hạt sen hoặc cháo gạo tẻ rây mịn kết hợp một chút dầu oliu hạt óc chó. Bí đỏ giàu tryptophan giúp sản sinh hormone ngủ ngon tự nhiên, hạt sen làm dịu hệ thần kinh non nớt.",
                "banner": "CÔNG THỨC CHÁO BÍ ĐỎ HẠT SEN ÊM BỤNG",
                "badge": "🥣 THỰC ĐƠN VÀNG CHO GIẤC NGỦ",
                "bullets": [
                    "Bí đỏ giàu Tryptophan: Kích thích hormone melatonin ngủ ngon",
                    "Hạt sen ninh nhừ: Làm dịu thần kinh, giúp bé ngủ sâu giấc",
                    "Dầu hạt óc chó: Bổ sung Omega 3 phát triển trí não ban đêm"
                ],
                "cta": "Bát cháo thơm ngậy giúp con ngủ ngoan một mạch!"
            },
            {
                "id": "scene_04",
                "voice": "Mẹ nhớ cho con ăn bữa tối trước giờ đi ngủ ít nhất một tiếng rưỡi đến hai tiếng nhé. Hãy bấm Follow kênh Ăn dặm mẹ Dâu để nhận thực đơn ăn tối ngon miệng, ấm bụng cho con mỗi ngày!",
                "banner": "QUY TẮC GIỜ ĂN TỐI CHUẨN Y KHOA",
                "badge": "⏰ NGUYÊN TẮC GIỜ GIẤC VÀNG",
                "bullets": [
                    "Khoảng cách vàng: Ăn trước giờ ngủ ít nhất 1.5 đến 2 tiếng",
                    "Không ép ăn no căng: Giữ lượng ăn vừa phải nhẹ nhàng",
                    "Vỗ ợ hơi cẩn thận: Giúp giải phóng bọt khí trước khi đặt nằm"
                ],
                "cta": "👉 Bấm Follow kênh để xem thêm thực đơn giấc ngủ cho bé!"
            }
        ]
    },
    8: {
        "title": "Bổ Sung Vi Chất Đúng Liều #1",
        "color": (41, 128, 185),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "D3K2, Sắt, Canxi hay Men vi sinh... Mẹ mua đủ cả bộ đắt tiền nhưng cho con uống vào lúc nào trong ngày để hấp thu tối đa mà không bị nóng trong hay nôn trớ? Xem ngay để không phí tiền mẹ nhé!",
                "banner": "D3K2, SẮT, CANXI: UỐNG GIỜ NÀO ĐỂ KHÔNG PHÍ TIỀN?",
                "badge": "💊 BỔ SUNG VI CHẤT ĐÚNG CÁCH",
                "bullets": [
                    "Bộ vi chất thiết yếu: D3K2, Sắt, Canxi, Men vi sinh",
                    "Băn khoăn của mẹ: Uống lúc nào, uống chung được không?",
                    "Rủi ro uống sai giờ: Giảm hấp thu, gây táo bón và nôn trớ"
                ],
                "cta": "Xem ngay cơ chế hấp thu của từng loại vi chất nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Mỗi loại vi chất đều có một kênh hấp thu riêng biệt. Vitamin D3K2 tan trong dầu, bắt buộc uống vào buổi sáng cùng cữ sữa hoặc bữa ăn có chất béo. Sắt hấp thu tốt nhất lúc bụng đói và đặc biệt bị ức chế hấp thu bởi canxi trong sữa.",
                "banner": "CƠ CHẾ HẤP THU & SỰ CẠNH TRANH VI CHẤT",
                "badge": "🔬 CƠ CHẾ HẤP THU ĐẶC BIỆT",
                "bullets": [
                    "D3K2 tan trong dầu: Cần chất béo từ sữa mẹ để hấp thu",
                    "Sắt ức chế bởi Canxi: Uống chung với sữa sẽ bị triệt tiêu",
                    "Khung giờ sinh học: Cơ thể hấp thu từng chất vào giờ khác nhau"
                ],
                "cta": "Lưu ngay lịch trình uống chuẩn y khoa dưới đây nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Lịch trình chuẩn y khoa cho con là: Tám giờ sáng, nhỏ một giọt D3K2 ngay sau cữ sữa đầu tiên. Mười giờ sáng, bổ sung sắt cách cữ sữa ít nhất một tiếng rưỡi. Và men vi sinh nên uống sau bữa ăn ba mươi phút để bảo vệ lợi khuẩn qua dịch vị dạ dày.",
                "banner": "LỊCH TRÌNH UỐNG VI CHẤT CHUẨN Y KHOA TRONG NGÀY",
                "badge": "⏰ THỜI GIAN BIỂU VÀNG TRONG NGÀY",
                "bullets": [
                    "08:00 Sáng: Nhỏ 1 giọt D3K2 sau cữ bú đầu tiên",
                    "10:00 Sáng: Uống Sắt cách xa cữ sữa ít nhất 1.5 tiếng",
                    "14:30 Chiều: Uống Men vi sinh sau bữa ăn 30 phút"
                ],
                "cta": "Con sẽ hấp thu 100% không lo táo bón!"
            },
            {
                "id": "scene_04",
                "voice": "Tuyệt đối không tự ý tăng liều vi chất khi chưa có chỉ định của bác sĩ mẹ nhé. Hãy bấm Follow kênh Ăn dặm mẹ Dâu để nắm trọn bí quyết bổ sung vi chất vàng cho con phát triển chiều cao!",
                "banner": "CẢNH BÁO AN TOÀN VỀ LIỀU LƯỢNG",
                "badge": "⚠️ NGUYÊN TẮC AN TOÀN TUYỆT ĐỐI",
                "bullets": [
                    "Đúng liều khuyến cáo: Không tự ý tăng giọt khi con ốm",
                    "Tham khảo ý kiến bác sĩ: Xét nghiệm vi chất khi cần thiết",
                    "Bảo quản chuẩn: Tránh ánh nắng trực tiếp, đậy kín nắp"
                ],
                "cta": "👉 Bấm Follow kênh để xem thêm cẩm nang vi chất cho bé!"
            }
        ]
    },
    9: {
        "title": "Mẹo Trữ Đông Thực Phẩm Chuẩn An Toàn Ngày 1",
        "color": (155, 89, 182),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Nấu một bữa ăn dặm cho con mất cả tiếng đồng hồ, nên mẹ bỉm nào cũng muốn nấu một lần trữ đông ăn cả tuần. Nhưng nếu mẹ trữ đông và rã đông sai cách, vi khuẩn sẽ sinh sôi gấp mười lần và làm mất sạch vitamin quý giá!",
                "banner": "TRỮ ĐÔNG ĐỒ ĂN DẶM: CẢNH BÁO VI KHUẨN PHÁT TRIỂN",
                "badge": "🧊 CẢNH BÁO VỆ SINH AN TOÀN",
                "bullets": [
                    "Nỗi vất vả nấu nướng: Mỗi bữa mất cả tiếng rây cháo, xay thịt",
                    "Giải pháp trữ đông: Giúp mẹ nhàn tênh, tiết kiệm thời gian",
                    "Mối nguy nếu làm sai: Vi khuẩn phát triển, ngộ độc đường ruột"
                ],
                "cta": "Xem ngay quy tắc chia khay và bảo quản chuẩn y tế nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Thức ăn của bé cần được chia nhỏ thành từng viên khẩu phần vào khay silicone có nắp kín ngay khi vừa nguội bớt. Tuyệt đối không để thức ăn ở nhiệt độ phòng quá hai tiếng vì vi khuẩn đường ruột phát triển cực nhanh trong dải nhiệt độ này.",
                "banner": "QUY TẮC KHAY SILICONE & DẢI NHIỆT ĐỘ NGUY HIỂM",
                "badge": "🔬 NGUYÊN TẮC NHIỆT ĐỘ BẢO QUẢN",
                "bullets": [
                    "Khay Silicone có nắp: Chất liệu an toàn không thôi nhiễm BPA",
                    "Chia từng viên khẩu phần: Tiện lấy đúng lượng ăn mỗi bữa",
                    "Quy tắc 2 giờ: Không để thức ăn ở ngoài phòng quá 2 tiếng"
                ],
                "cta": "Lưu lại thời hạn vàng bảo quản dưới đây mẹ nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Quy tắc thời hạn bảo quản vàng: Ngăn mát bảo quản tối đa hai mươi tư giờ, ngăn đông dưới âm mười tám độ dùng tốt nhất trong vòng hai tuần. Khi rã đông, mẹ chuyển xuống ngăn mát từ đêm hôm trước hoặc hấp cách thủy, tuyệt đối không rã đông ở nhiệt độ phòng rồi cấp đông lại!",
                "banner": "THỜI HẠN BẢO QUẢN & CÁCH RÃ ĐÔNG AN TOÀN",
                "badge": "❄️ THỜI HẠN VÀNG & CÁCH RÃ ĐÔNG",
                "bullets": [
                    "Ngăn mát: Dùng hết trong vòng 24 đến 48 giờ tối đa",
                    "Ngăn đông (-18°C): Bảo quản tốt nhất trong vòng 2 tuần",
                    "Rã đông an toàn: Để ngăn mát qua đêm hoặc hấp cách thủy"
                ],
                "cta": "Tuyệt đối không tái cấp đông đồ đã rã đông mẹ nhé!"
            },
            {
                "id": "scene_04",
                "voice": "Một chút cẩn thận trong khâu bảo quản sẽ giữ trọn dưỡng chất và bảo vệ đường ruột non nớt của con. Bấm Follow kênh Ăn dặm mẹ Dâu để cùng mẹ chăm con nhàn tênh mà an toàn tuyệt đối nhé!",
                "banner": "CHĂM CON NHÀN TÊNH MÀ VẪN AN TOÀN",
                "badge": "🌟 BÍ QUYẾT MẸ BỈM THÔNG THÁI",
                "bullets": [
                    "Dán nhãn ngày nấu: Kiểm soát hạn dùng chuẩn xác từng hộp",
                    "Giữ trọn vi chất: Không đun sôi cháo nhiều lần làm mất vitamin",
                    "Mẹ thảnh thơi chăm con: Dành nhiều thời gian chơi cùng bé yêu"
                ],
                "cta": "👉 Bấm Follow kênh để xem thêm mẹo bếp núc ăn dặm nhé!"
            }
        ]
    },
    10: {
        "title": "Nuôi Con Không Phải Cuộc Chiến #1",
        "color": (142, 68, 173),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Mỗi bữa ăn dặm của con là một niềm vui khám phá hay đang là một cuộc chiến đầy nước mắt, với tiếng quát mắng, tiếng gõ bát đĩa và chiếc điện thoại bật hoạt hình inh ỏi khắp nhà?",
                "banner": "BỮA ĂN CỦA CON LÀ NIỀM VUI HAY CUỘC CHIẾN?",
                "badge": "💔 NỖI ÁM ẢNH BỮA ĂN GIA ĐÌNH",
                "bullets": [
                    "Thực trạng đau lòng: Tiếng la mắng, ép ăn, con gào khóc",
                    "Điện thoại & Tivi: Bật inh ỏi để lừa con há miệng nuốt chửng",
                    "Hệ quả tâm lý: Con sợ hãi giờ ăn, mất phản xạ no đói tự nhiên"
                ],
                "cta": "Xem ngay nguyên tắc vàng của chuyên gia dinh dưỡng nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Tiến sĩ Ellyn Satter đã đưa ra nguyên tắc vàng trong nuôi con: Bố mẹ chịu trách nhiệm quyết định con ăn món gì, ăn ở đâu và khi nào. Còn con có toàn quyền quyết định mình ăn bao nhiêu và có ăn món đó hay không. Ép ăn chỉ tạo ra nỗi sợ hãi tột cùng.",
                "banner": "NGUYÊN TẮC PHÂN CHIA TRÁCH NHIỆM BÀN ĂN",
                "badge": "🔬 NGUYÊN TẮC CỦA TS ELLYN SATTER",
                "bullets": [
                    "Quyền của bố mẹ: Quyết định ăn món gì, ăn ở đâu, vào giờ nào",
                    "Quyền của con: Quyết định ăn bao nhiêu và ăn món nào",
                    "Tôn trọng cơ thể bé: Dạ dày con biết chính xác khi nào no"
                ],
                "cta": "Áp dụng 3 bước giải phóng áp lực cho cả mẹ và bé nhé!"
            },
            {
                "id": "scene_03",
                "voice": "Ba bước để giải phóng mẹ khỏi áp lực: Thứ nhất, tuyệt đối không cho con xem tivi điện thoại khi ăn. Thứ hai, tôn trọng tín hiệu no của con: khi con ngậm chặt miệng hay lắc đầu, hãy dọn bàn ăn trong vui vẻ. Thứ ba, cho con ngồi chung bàn ăn với gia đình để khơi dậy bản năng bắt chước.",
                "banner": "3 BƯỚC BIẾN BỮA ĂN THÀNH NIỀM HẠNH PHÚC",
                "badge": "🌟 3 BƯỚC THIẾT LẬP NỀN NẾP ĂN",
                "bullets": [
                    "Bước 1: Tắt hoàn toàn tivi điện thoại, tập trung vào đĩa ăn",
                    "Bước 2: Dọn bàn trong vui vẻ khi con lắc đầu hoặc ngậm miệng",
                    "Bước 3: Cho con ngồi ghế ăn dặm chung mâm cùng cả nhà"
                ],
                "cta": "Con sẽ tìm lại niềm vui tự giác ăn uống!"
            },
            {
                "id": "scene_04",
                "voice": "Một em bé vui vẻ, hào hứng với thức ăn quan trọng hơn rất nhiều một bát cháo đầy ắp mẹ nhé. Ăn dặm mẹ Dâu luôn ở đây để lắng nghe và đồng hành cùng mẹ, hãy bấm Follow kênh ngay hôm nay!",
                "banner": "HẠNH PHÚC CỦA MỘT EM BÉ ĂN TRONG VUI VẺ",
                "badge": "💖 LỜI NHẮC NHỞ ẤM ÁP TỪ MẸ DÂU",
                "bullets": [
                    "Không so sánh cân nặng: Mỗi em bé có một biểu đồ phát triển riêng",
                    "Ăn là niềm vui: Khám phá hương vị thế giới trong hạnh phúc",
                    "Đồng hành thấu hiểu: Mẹ Dâu luôn sẻ chia cùng mẹ bỉm"
                ],
                "cta": "👉 Bấm Follow kênh để cùng nuôi con vui vẻ mỗi ngày!"
            }
        ]
    },
    11: {
        "title": "Bát Cháo Đầu Tiên Và Giọt Nước Mắt Của Mẹ",
        "color": (217, 83, 79),
        "scenes": [
            {
                "id": "scene_01",
                "voice": "Có mẹ nào giống như mình không? Đêm trước ngày con tròn sáu tháng, mẹ thức trắng đêm đọc tài liệu, hồi hộp và lo lắng đến mức sáng hôm sau bê bát cháo đầu đời của con mà tay run lẩy bẩy...",
                "banner": "BÁT CHÁO ĐẦU TIÊN VÀ TAY MẸ RUN LẨY BẨY",
                "badge": "🥺 TÂM TƯ NGƯỜI MẸ ĐÊM KHỞI ĐẦU",
                "bullets": [
                    "Đêm thức trắng: Đọc từng trang tài liệu, loay hoay chuẩn bị bát thìa",
                    "Nỗi lo lắng thiêng liêng: Sợ nấu không đúng, sợ con không chịu ăn",
                    "Khoảnh khắc bỡ ngỡ: Bê bát cháo trên tay mà tim đập thình thịch"
                ],
                "cta": "Cùng sống lại khoảnh khắc kỳ diệu đầu đời của con nhé!"
            },
            {
                "id": "scene_02",
                "voice": "Mẹ cẩn thận rây từng hạt gạo trắng ngần cho thật mịn, rồi nhẹ nhàng đưa thìa cháo đến gần môi con. Khoảnh khắc nhìn con tròn xoe mắt ngơ ngác nếm giọt cháo đầu tiên, rồi chun mũi nuốt trọn, bao nhiêu mệt mỏi sau những đêm thức trắng chăm con bỗng tan biến thành nụ cười.",
                "banner": "KHOẢNH KHẮC CON NẾM GIỌT CHÁO ĐẦU TIÊN",
                "badge": "✨ KHOẢNH KHẮC KỲ DIỆU ĐẦU ĐỜI",
                "bullets": [
                    "Tỉ mỉ từng hạt gạo: Rây cháo mịn màng như dòng sữa mẹ",
                    "Ánh mắt ngơ ngác: Con tròn xoe mắt chạm vào hương vị mới",
                    "Chun mũi nuốt trọn: Mọi nhọc nhằn thức đêm bỗng hóa nụ cười"
                ],
                "cta": "Khoảnh khắc ấy mẹ sẽ nhớ mãi suốt cuộc đời!"
            },
            {
                "id": "scene_03",
                "voice": "Dù hôm nay con ăn hết cả thìa cháo hay nhè ra áo lấm lem, thì mẹ vẫn thấy tự hào vô cùng. Con của mẹ đã chính thức lớn khôn, bước sang một trang đời mới, không còn chỉ bám lấy bầu sữa mẹ nữa, mà bắt đầu tự mình khám phá hương vị thế giới bao la.",
                "banner": "TẤM LÒNG NGƯỜI MẸ TRÊN BƯỚC ĐƯỜNG CON LỚN",
                "badge": "💌 LỜI THỔ LỘ CỦA MẸ BỈM",
                "bullets": [
                    "Ăn hết hay nhè ra: Mẹ vẫn mỉm cười ôm con vào lòng",
                    "Con lớn thật rồi: Bước sang một trang đời mới đầy kỳ thú",
                    "Tự mình khám phá: Thế giới bao la đang chờ đón bước chân con"
                ],
                "cta": "Mẹ sẽ luôn là điểm tựa vững chắc cho con!"
            },
            {
                "id": "scene_04",
                "voice": "Tối nay mẹ hãy ôm con thật chặt và tự khen mình một câu nhé: Mẹ đã làm rất tuyệt vời rồi! Hãy bấm Follow kênh Ăn dặm mẹ Dâu để cùng mẹ sẻ chia những khoảnh khắc làm mẹ thiêng liêng nhất mỗi ngày!",
                "banner": "TỐI NAY MẸ HÃY ÔM CON THẬT CHẶT NHÉ!",
                "badge": "💖 MẸ ĐÃ LÀM RẤT TUYỆT VỜI RỒI!",
                "bullets": [
                    "Lời vỗ về cho mẹ: Đừng tự trách mình vì những vụng về đầu tiên",
                    "Ôm con thật chặt: Cảm nhận hơi ấm thiêng liêng của tình mẫu tử",
                    "Cùng nhau trưởng thành: Mỗi ngày làm mẹ là một ngày học yêu thương"
                ],
                "cta": "👉 Bấm Follow kênh để cùng tâm tình mỗi tối mẹ nhé!"
            }
        ]
    }
}

def produce_slot_xuan_dung(slot_id: int):
    config = SCENES_CONFIG.get(slot_id)
    if not config:
        print(f"Chưa có cấu hình 4 cảnh cho Slot {slot_id}")
        return

    title = config["title"]
    theme_color = config["color"]
    scenes_spec = config["scenes"]
    clean_t = clean_filename(title)

    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU SẢN XUẤT CHUẨN 4 CẢNH XUÂN DUNG: SLOT {slot_id} — {title}")
    print(f"=======================================================")

    project_dir = REPO_ROOT / "projects" / f"day_01_slot_{slot_id:02d}_xuan_dung"
    output_dir = project_dir / "output"
    audio_dir = output_dir / "audio-scenes"
    audio_dir.mkdir(parents=True, exist_ok=True)

    project_scenes = []
    project_narration = []

    # 1. Tạo 4 ảnh & annotations
    print("  [1/4] Thiết kế 4 ảnh phân cảnh đồ họa chuẩn 9:16...")
    for idx, sc in enumerate(scenes_spec, start=1):
        sc_id = sc["id"]
        sc_png = project_dir / f"{sc_id}.png"
        sc_ann_file = project_dir / f"{sc_id}.annotation.json"

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
            text=sc["voice"],
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

    # 3. Tạo giọng đọc Xuân Dung (OmniVoice Clean)
    print("  [2/4] Tạo giọng đọc Xuân Dung liền mạch 4 cảnh (OmniVoice Clean)...")
    scene_audio_map = generate_scene_voices(
        cli_path=CLI_PATH,
        project=project,
        reference_audio=VOICE_REF,
        output_dir=audio_dir,
        on_log=lambda msg: print(f"    [OmniVoice] {msg}"),
        cancel_event=threading.Event(),
        reference_text="Muốn đổi món với thịt bò cho bé, đây là 5 gợi ý dễ ăn.",
    )

    # 4. Biên dịch Timeline & Đồng bộ Whiteboard
    print("  [3/4] Biên dịch Timeline & Đồng bộ Whiteboard...")
    timeline_res = compile_scene_timeline(
        project=project,
        scene_audio=scene_audio_map,
        output_dir=output_dir,
        on_log=lambda m: None
    )
    project.voice = timeline_res.voice_path
    project.runtime_annotations = timeline_res.runtime_annotations
    duration_s = timeline_res.total_duration_ms / 1000
    print(f"    -> Thời lượng video dự kiến: {duration_s:.1f}s (Chuẩn 30-50s!)")

    # 5. Render video vẽ tay GPU (2K 1440x2560)
    print("  [4/4] Render video vẽ tay GPU (2K 1440x2560)...")
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

    # 6. Export to Google Drive
    drive_dest = DRIVE_DIR / f"Day_01_Slot_{slot_id:02d}_{clean_t}_2K.mp4"
    shutil.copy2(final_mp4, drive_dest)
    print(f"  ✅ ĐÃ XUẤT FILE SANG DRIVE: {drive_dest} ({drive_dest.stat().st_size / (1024*1024):.2f} MB, {duration_s:.1f}s)")

    # 7. Update Google Sheets Webhook
    update_google_sheets(
        day=1,
        slot_id=slot_id,
        video_path=str(drive_dest),
        status=f"READY_TO_PUBLISH (2K 1440x2560 - {duration_s:.1f}s)"
    )
    print(f"  🎉 HOÀN THÀNH XUẤT BẢN CHO SLOT {slot_id} BẰNG GIỌNG XUÂN DUNG!\n")

def run_all_day01_slots():
    # Chạy lần lượt các slot từ 3 đến 11
    slots = list(range(3, 12))
    print(f"Chuẩn bị sản xuất tự động {len(slots)} slot còn lại (Slot 3 đến 11)...")
    for s in slots:
        try:
            produce_slot_xuan_dung(s)
        except Exception as e:
            print(f"❌ LỖI KHI XỬ LÝ SLOT {s}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        run_all_day01_slots()
    elif len(sys.argv) > 1:
        produce_slot_xuan_dung(int(sys.argv[1]))
    else:
        run_all_day01_slots()
