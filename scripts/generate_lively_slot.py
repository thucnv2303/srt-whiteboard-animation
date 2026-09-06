"""
scripts/generate_lively_slot.py - Công cụ CLI sản xuất video chuẩn Tiêu Chuẩn Vàng cho bất kỳ Slot nào trong 330 Video.

Cách sử dụng:
  # Chạy 1 slot cụ thể (mặc định Day 1 Slot 2):
  python scripts/generate_lively_slot.py --day 1 --slot 2

  # Chạy thử với độ phân giải 1080p:
  python scripts/generate_lively_slot.py --day 1 --slot 2 --aspect-ratio "9:16"
"""

import argparse
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from whiteboard_app.slot_builder import load_slot_from_plan, GoldenSlotBuilder

def main():
    parser = argparse.ArgumentParser(description="Tạo video theo Tiêu Chuẩn Vàng cho bất kỳ Slot nào")
    parser.add_argument("--day", type=int, default=1, help="Ngày trong kế hoạch (1-30)")
    parser.add_argument("--slot", type=int, default=2, help="Slot ID trong ngày (1-11)")
    parser.add_argument("--aspect-ratio", type=str, default="9:16 2K", help="Độ phân giải (9:16 2K, 9:16, 16:9 2K, 1:1 2K)")
    parser.add_argument("--gaze-ms", type=int, default=1000, help="Thời gian dừng tĩnh cuối cảnh (ms)")
    args = parser.parse_args()

    print(f"=== KHỞI CHẠY TIÊU CHUẨN VÀNG: NGÀY {args.day} - SLOT {args.slot} ===")
    slot_data = load_slot_from_plan(args.day, args.slot)
    if not slot_data:
        print(f"Lỗi: Không tìm thấy Ngày {args.day} Slot {args.slot} trong kế hoạch CSV!")
        sys.exit(1)

    print(f"  Tiêu đề: {slot_data.title}")
    print(f"  Chuyên mục: {slot_data.pillar} ({slot_data.slot_name})")

    project_dir = REPO_ROOT / "projects" / f"day_{args.day:02d}_slot_{args.slot:02d}_golden"
    raw_gpt_dir = project_dir / "raw_gpt_images"

    # Thư mục gốc ảnh nền minh họa (ưu tiên Input pic hoặc raw_gpt_images)
    d_str = f"{args.day:02d}"
    s_str = f"{args.slot:02d}"
    input_pic_dir = REPO_ROOT / "Input pic"
    input_f1 = input_pic_dir / f"day_{d_str}_slot_{s_str}_scene_01.jpg"
    std_f1 = raw_gpt_dir / f"day_{d_str}_slot_{s_str}_scene_01.jpg"
    std_f1_png = raw_gpt_dir / f"day_{d_str}_slot_{s_str}_scene_01.png"

    if input_pic_dir.is_dir() and input_f1.is_file() and input_f1.stat().st_size > 0:
        base_images = [
            input_pic_dir / f"day_{d_str}_slot_{s_str}_scene_{c:02d}.jpg"
            for c in range(1, 5)
        ]
        print(f"  Đang sử dụng bộ ảnh vẽ tay nghệ thuật GPT từ: {input_pic_dir}")
    elif raw_gpt_dir.is_dir() and (std_f1.is_file() or std_f1_png.is_file()):
        ext = ".jpg" if std_f1.is_file() else ".png"
        base_images = [
            raw_gpt_dir / f"day_{d_str}_slot_{s_str}_scene_{c:02d}{ext}"
            for c in range(1, 5)
        ]
        print(f"  Đang sử dụng bộ ảnh vẽ tay nghệ thuật GPT (tên chuẩn) từ: {raw_gpt_dir}")
    elif raw_gpt_dir.is_dir() and (raw_gpt_dir / "s1.jpg").is_file():
        base_images = [
            raw_gpt_dir / f"s{c}.jpg"
            for c in range(1, 5)
        ]
        print(f"  Đang sử dụng bộ ảnh vẽ tay nghệ thuật GPT từ: {raw_gpt_dir}")
    else:
        img_dir = REPO_ROOT / "projects" / "day_01_an_dam_v2"
        base_images = [
            img_dir / "scene_01.png",
            img_dir / "scene_02.png",
            img_dir / "scene_03.png",
            img_dir / "scene_04.png"
        ]

    builder = GoldenSlotBuilder(
        slot_data=slot_data,
        base_images=base_images,
        project_dir=project_dir,
        gaze_ms=args.gaze_ms,
        aspect_ratio=args.aspect_ratio
    )

    # Cấu hình kịch bản và đồ họa 4 cảnh
    if args.day == 1 and args.slot == 2:
        script_scenes_cfg = [
            {
                "title": "BỮA ĂN DẶM ĐẦU TIÊN CỦA BÉ 6 THÁNG",
                "alert_title": "TUYỆT ĐỐI KHÔNG TRỘN NẾP & HẠT SEN!",
                "alert_bullet1": "• Bé 6 tháng chưa có men tiêu hóa tinh bột dẻo",
                "alert_bullet2": "• Gây trướng bụng, đầy hơi, nôn trớ & sợ ăn dặm",
                "warn_label": "CẢNH BÁO Y KHOA: CẤM NẾP & HẠT SEN",
                "gas_label": "KHÍ TRƯỚNG Ứ ĐỌNG"
            },
            {
                "title": "TẠI SAO BÉ CHƯA THỂ ĂN GẠO NẾP?",
                "good_title": "CHÁO GẠO TẺ RÂY 1:10 — DỄ TIÊU HÓA",
                "good_desc": "Dạ dày 6 tháng chỉ bằng quả trứng, hấp thu êm dịu",
                "bad_title": "GẠO NẾP & HẠT SEN — QUÁ TẢI TIÊU HÓA!",
                "bad_desc": "Thiếu men amylase, gây ứ đọng, trướng bụng & nôn trớ",
                "bot_title": "LỰA CHỌN DUY NHẤT: GẠO TẺ TRẮNG NGUYÊN CÁM",
                "bot_desc": "Bảo vệ tối đa niêm mạc ruột và hệ vi sinh của con"
            },
            {
                "title": "CÔNG THỨC CHÁO RÂY 1:10 CHUẨN Y KHOA",
                "step1_title": "BƯỚC 1: GẠO TẺ NGUYÊN CÁM",
                "step1_desc": "Chọn gạo thơm mới, vo nhẹ 1 lần giữ vitamin B1",
                "step1_tag": "VITAMIN B1",
                "step2_title": "BƯỚC 2: TỶ LỆ VÀNG 1 : 10",
                "step2_desc": "Đong 10g gạo với 100ml nước, ninh nhỏ lửa 45 phút",
                "step2_tag": "NINH 45 PHÚT",
                "step3_title": "BƯỚC 3: RÂY MỊN KHI ẤM NÓNG",
                "step3_desc": "Rây qua lưới 0.5mm, miết lưng thìa lấy cháo sánh",
                "step3_tag": "LƯỚI 0.5MM"
            },
            {
                "title": "NGUYÊN TẮC VÀNG BỮA ĐẦU TIÊN",
                "badge1_label": "1 - 2 THÌA CÀ PHÊ NHỎ (5ML)",
                "badge2_label": "ĂN CỮ SÁNG: 9H - 10H VUI VẺ",
                "badge3_label": "THEO DÕI PHÂN & DA 3 NGÀY",
                "nosalt_text": "TUYỆT ĐỐI KHÔNG NÊM MẮM, MUỐI, DẦU ĂN",
                "cta_title": "BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!",
                "cta_sub": "Đồng hành chăm con khỏe mạnh chuẩn y khoa"
            }
        ]
        scripts_text = [
            "Rất nhiều mẹ hỏi Mẹ Dâu: Bé tròn sáu tháng bắt đầu ăn dặm, có nên trộn thêm gạo nếp, hạt sen hay đậu xanh vào nấu cháo cho con nhanh tăng cân không? Câu trả lời dứt khoát là tuyệt đối không mẹ nhé! Đây là sai lầm kinh điển khiến hệ tiêu hóa non nớt của con bị quá tải ngay từ bữa đầu tiên.",
            "Mẹ biết không, dạ dày bé sáu tháng chỉ nhỏ bằng một quả trứng gà. Tuyến tụy của con mới chỉ tiết một lượng rất ít men amylase để phân giải tinh bột thuần từ gạo tẻ. Tinh bột amylopectin trong gạo nếp lại cực kỳ khó cắt đứt liên kết, còn hạt sen lại chứa hàm lượng chất đạm thực vật phức tạp. Trộn vào lúc này sẽ khiến đường ruột con bị lên men ứ đọng, gây chướng bụng, quấy khóc cả đêm và nôn trớ sợ ăn.",
            "Để con có bữa ăn đầu đời hoàn hảo, mẹ làm đúng ba bước sau: Bước một: Chọn gạo tẻ thơm nguyên cám giàu vitamin nhóm B, chỉ vo nhẹ tay một lần với nước sạch để giữ trọn dưỡng chất. Bước hai: Đong chuẩn mười gam gạo với một trăm mililít nước theo đúng tỷ lệ vàng một mười kiểu Nhật. Ninh lửa nhỏ liu riu trong bốn mươi lăm phút cho hạt gạo nở bung mềm nhừ. Bước ba: Khi cháo còn ấm nóng, mẹ đổ qua rây mắt nhỏ không phẩy năm milimét, dùng lưng thìa miết nhẹ hai lần. Phần cháo thu được sẽ sánh mịn đồng nhất như sữa mẹ, giúp con nuốt êm ái mà không sợ nghẹn hóc.",
            "Bữa đầu tiên, mẹ chỉ cho con nếm thử một đến hai thìa cà phê nhỏ vào cữ sáng khi con tỉnh táo. Tuyệt đối không nêm bất kỳ giọt mắm, muối hay dầu ăn nào vì thận của con chưa lọc được mẹ nhé. Sau ăn, mẹ quan sát phân và da con trong ba ngày liên tiếp. Mẹ hãy bấm lưu video và Follow Ăn dặm mẹ Dâu để cùng mẹ đồng hành chăm con chuẩn y khoa nhé!"
        ]
    else:
        # Tự động sinh cấu trúc chuẩn cho các slot khác dựa vào Hook - Body - CTA
        script_scenes_cfg = [
            {
                "title": slot_data.title.upper(),
                "alert_title": "CẢNH BÁO SAI LẦM PHỔ BIẾN!",
                "alert_bullet1": "• Không tự ý làm theo kinh nghiệm truyền miệng",
                "alert_bullet2": "• Bảo vệ đường ruột và thận non nớt của con",
                "warn_label": "KHUYẾN CÁO Y KHOA CHUẨN WHO",
                "gas_label": "CẨN TRỌNG TIÊU HÓA"
            },
            {
                "title": "CƠ CHẾ SINH LÝ HỆ TIÊU HÓA BÉ",
                "good_title": "PHƯƠNG PHÁP ĐÚNG — HẤP THU ÊM DỊU",
                "good_desc": "Hệ tiêu hóa khỏe mạnh giúp bé tăng cân tự nhiên",
                "bad_title": "SAI PHƯƠNG PHÁP — GÁNH NẶNG NỘI TẠNG!",
                "bad_desc": "Dễ gây rối loạn tiêu hóa và biếng ăn tâm lý",
                "bot_title": "NGUYÊN TẮC: TỪ ÍT ĐẾN NHIỀU, TỪ LOÃNG ĐẾN ĐẶC",
                "bot_desc": "Luôn lắng nghe tín hiệu no đói tự nhiên của con"
            },
            {
                "title": "HƯỚNG DẪN 3 BƯỚC THỰC HÀNH CHUẨN",
                "step1_title": "BƯỚC 1: CHỌN VÀ SƠ CHẾ NGUYÊN LIỆU",
                "step1_desc": "Nguyên liệu tươi mới, giữ trọn vi chất tự nhiên",
                "step1_tag": "CHUẨN VI CHẤT",
                "step2_title": "BƯỚC 2: CHẾ BIẾN THEO ĐỘ THÔ PHÙ HỢP",
                "step2_desc": "Không xay nhuyễn quá lâu, tăng thô đúng tháng tuổi",
                "step2_tag": "TĂNG ĐỘ THÔ",
                "step3_title": "BƯỚC 3: KIỂM TRA ĐỘ MỊN VÀ NHIỆT ĐỘ",
                "step3_desc": "Thử nhiệt độ ấm vừa phải trước khi đút cho con",
                "step3_tag": "NHIỆT ĐỘ ẤM"
            },
            {
                "title": "LỜI KHUYÊN VÀNG CỦA MẸ DÂU",
                "badge1_label": "ĐỊNH LƯỢNG VỪA SỨC BÉ",
                "badge2_label": "KHÔNG ÉP ĂN TẠO ÁP LỰC",
                "badge3_label": "THEO DÕI PHẢN ỨNG CỦA CON",
                "nosalt_text": "TUYỆT ĐỐI KHÔNG NÊM GIA VỊ DƯỚI 1 TUỔI",
                "cta_title": "BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!",
                "cta_sub": "Đồng hành chăm con khỏe mạnh chuẩn y khoa"
            }
        ]
        scripts_text = [
            slot_data.hook,
            f"Mẹ biết không, {slot_data.body[:len(slot_data.body)//2]}",
            f"Chính vì vậy, {slot_data.body[len(slot_data.body)//2:]}",
            slot_data.cta
        ]

    result_path = builder.run_pipeline(script_scenes_cfg, scripts_text)
    if result_path:
        print(f"\n[OK] HOÀN TẤT XUẤT SẮC SLOT {args.slot} NGÀY {args.day}!")
        print(f"  Đường dẫn: {result_path}")
    else:
        print(f"\n[FAIL] SẢN XUẤT THẤT BẠI CHO SLOT {args.slot} NGÀY {args.day}!")
        sys.exit(1)

if __name__ == "__main__":
    main()
