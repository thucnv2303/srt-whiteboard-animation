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
        base_images = []
        for c in range(1, 5):
            f_jpg = input_pic_dir / f"day_{d_str}_slot_{s_str}_scene_{c:02d}.jpg"
            f_png = input_pic_dir / f"day_{d_str}_slot_{s_str}_scene_{c:02d}.png"
            if f_jpg.is_file() and f_jpg.stat().st_size > 0:
                base_images.append(f_jpg)
            elif f_png.is_file() and f_png.stat().st_size > 0:
                base_images.append(f_png)
            else:
                base_images.append(f_jpg)
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

    from whiteboard_app.day_01_configs import DAY_01_CONFIGS

    # Cấu hình kịch bản và đồ họa 4 cảnh chuyên sâu chuẩn Tiêu Chuẩn Vàng
    if args.day == 1 and args.slot in DAY_01_CONFIGS:
        slot_cfg = DAY_01_CONFIGS[args.slot]
        script_scenes_cfg = slot_cfg["scenes_cfg"]
        scripts_text = slot_cfg["scripts_text"]
        print(f"  ✨ Đã nạp Kịch bản Y Khoa Chuyên Sâu & Đồ Họa Riêng Biệt cho Slot {args.slot:02d}!")
    else:
        # Fallback tự động sinh cấu trúc chuẩn cho các ngày khác dựa vào Hook - Body - CTA
        script_scenes_cfg = [
            {
                "title": slot_data.title.upper(),
                "alert_title": "CẢNH BÁO SAI LẦM PHỔ BIẾN!",
                "alert_bullet1": "• Không tự ý làm theo kinh nghiệm truyền miệng",
                "alert_bullet2": "• Bảo vệ đường ruột và thận non nớt của con",
                "warn_label": "KHUYẾN CÁO Y KHOA CHUẨN WHO",
                "bot_title": "NGUYÊN TẮC: TỪ ÍT ĐẾN NHIỀU, TỪ LOÃNG ĐẾN ĐẶC",
                "bot_desc": "Luôn lắng nghe tín hiệu no đói tự nhiên của con"
            },
            {
                "title": "CƠ CHẾ SINH LÝ HỆ TIÊU HÓA BÉ",
                "good_title": "PHƯƠNG PHÁP ĐÚNG — HẤP THU ÊM DỊU",
                "good_desc": "Hệ tiêu hóa khỏe mạnh giúp bé tăng cân tự nhiên",
                "bad_title": "SAI PHƯƠNG PHÁP — GÁNH NẶNG NỘI TẠNG!",
                "bad_desc": "Dễ gây rối loạn tiêu hóa và biếng ăn tâm lý"
            },
            {
                "title": "HƯỚNG DẪN 3 BƯỚC THỰC HÀNH CHUẨN",
                "step1_title": "BƯỚC 1: SƠ CHẾ NGUYÊN LIỆU",
                "step1_desc": ["Nguyên liệu tươi mới", "Giữ trọn vi chất tự nhiên"],
                "step1_tag": "CHUẨN VI CHẤT",
                "step2_title": "BƯỚC 2: CHẾ BIẾN ĐỘ THÔ PHÙ HỢP",
                "step2_desc": ["Không xay nhuyễn quá lâu", "Tăng thô đúng tháng tuổi"],
                "step2_tag": "TĂNG ĐỘ THÔ",
                "step3_title": "BƯỚC 3: KIỂM TRA ĐỘ ẤM",
                "step3_desc": ["Thử nhiệt độ ấm vừa phải", "Để con nuốt êm ái tự nhiên"],
                "step3_tag": "NHIỆT ĐỘ ẤM"
            },
            {
                "title": "LỜI KHUYÊN VÀNG CỦA MẸ DÂU",
                "badge1_label": "ĐỊNH LƯỢNG VỪA SỨC BÉ",
                "badge2_label": "KHÔNG ÉP ĂN TẠO ÁP LỰC",
                "badge3_label": "THEO DÕI PHẢN ỨNG CỦA CON",
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
