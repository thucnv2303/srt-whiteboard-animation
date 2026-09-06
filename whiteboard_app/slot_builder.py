"""
whiteboard_app/slot_builder.py - Động cơ sản xuất Video chuẩn Tiêu Chuẩn Vàng (Golden Benchmark) cho mọi Slot.
Hỗ trợ:
- Lấy thông tin bất kỳ slot nào từ CSV (CONTENT_PLAN_30_DAYS_330_VIDEOS.csv) hoặc nhận cấu hình trực tiếp.
- Bố cục 4 cảnh nghệ thuật với các hình khối vẽ tay đa dạng (3D Ribbon, Comic Bubble, Washi Memo, Number Badges + Pill Tags, Capsule Heart CTA) và vector icons theo kịch bản (không dùng font emoji).
- Tạo giọng đọc liền mạch bằng OmniVoice Xuân Dung Clean (hoặc profile tùy chọn) theo từng cảnh.
- Căn chỉnh Timeline với Whisper (Keyword Alignment), nhịp xem thư thái với gaze_ms = 1000ms.
- Render GPU 2K 1440x2560 (hoặc 1080p), ghép chuyển trang slideleft.
- Xuất bản tự động sang Google Drive và đồng bộ Google Sheets Webhook.
"""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from PIL import Image, ImageDraw, ImageFont

from .art_shapes import (
    draw_fitted_text,
    draw_ribbon_banner,
    draw_speech_bubble,
    draw_washi_memo_card,
    draw_step_pill_badge,
    draw_cta_capsule,
    draw_prohibition_badge,
    draw_egg_size_badge,
    draw_scale_icon,
    draw_beaker_water,
    draw_clock_timer,
    draw_sieve_badge,
    draw_spoon_dosage,
    draw_sun_time_badge,
    draw_calendar_allergy_badge,
    draw_vector_heart,
    draw_vector_sun,
    draw_vector_spoon,
    draw_vector_calendar,
    draw_seamless_cloud,
    draw_torn_paper_card,
    draw_seamless_parchment,
    draw_seamless_rosette,
    draw_speech_balloon,
    draw_auto_card_text,
    draw_warning_pill,
    draw_advice_card,
    get_font,
    FONT_BOLD,
    FONT_REGULAR,
    THEME_COLOR,
    RED_COLOR,
    GREEN_COLOR,
    BLUE_COLOR,
    PAPER_BG
)
from .project import VideoProject, Scene, NarrationCue, _read_manifest
from .voice import VoiceLibrary, generate_scene_voices
from .timeline import compile_scene_timeline
from .renderer import build_commands, subprocess_environment

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_CSV_PATH = REPO_ROOT / "knowledge" / "an_dam_me_dau" / "CONTENT_PLAN_30_DAYS_330_VIDEOS.csv"
DEFAULT_VOICE_REF = Path(r"C:\Users\thucn\AppData\Roaming\NetChuyenDong\voices\62f4aecdb5fa4ad3b7edbc49865d5b9a.wav")
DEFAULT_CLI_PATH = r"C:/Users/thucn/AppData/Local/Programs/Python/Python311/Scripts/omnivoice-infer.exe"
DRIVE_OUTPUT_DIR = Path(r"G:\My Drive\Đăng video")
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycby0n2AFHNxWRE2CXlblJuFLm9dJoBzawmonnKkLXDAugrJvZz5WHhbkmWQT6qscAe3VyA/exec"


@dataclass
class SlotData:
    day: int
    slot_id: int
    slot_name: str
    pillar: str
    title: str
    hook: str
    body: str
    cta: str
    tiktok_caption: str
    reels_caption: str
    youtube_title: str
    youtube_description: str
    video_path: str
    status: str


def load_slot_from_plan(day: int, slot_id: int, csv_path: Path = PLAN_CSV_PATH) -> Optional[SlotData]:
    """Tìm nạp dữ liệu một slot cụ thể từ file kế hoạch 330 video."""
    if not csv_path.is_file():
        return None
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                r_day = int(row.get("day", 0))
                r_slot = int(row.get("slot_id", 0))
                if r_day == day and r_slot == slot_id:
                    return SlotData(
                        day=r_day,
                        slot_id=r_slot,
                        slot_name=row.get("slot", ""),
                        pillar=row.get("pillar", ""),
                        title=row.get("title", ""),
                        hook=row.get("hook", ""),
                        body=row.get("body", ""),
                        cta=row.get("cta", ""),
                        tiktok_caption=row.get("tiktok_caption", ""),
                        reels_caption=row.get("reels_caption", ""),
                        youtube_title=row.get("youtube_title", ""),
                        youtube_description=row.get("youtube_description", ""),
                        video_path=row.get("video_path", ""),
                        status=row.get("status", "PENDING")
                    )
            except (ValueError, TypeError):
                continue
    return None


class GoldenSlotBuilder:
    """Động cơ dựng video theo tiêu chuẩn vàng cho bất kỳ slot nào."""

    def __init__(
        self,
        slot_data: SlotData,
        base_images: list[Path],
        project_dir: Path,
        cli_path: str = DEFAULT_CLI_PATH,
        voice_ref: Path = DEFAULT_VOICE_REF,
        gaze_ms: int = 1000,
        aspect_ratio: str = "9:16 2K",
        on_log: Optional[Callable[[str], None]] = None
    ):
        self.slot = slot_data
        self.base_images = base_images
        self.project_dir = project_dir
        self.output_dir = project_dir / "output"
        self.audio_dir = self.output_dir / "audio-scenes"
        self.cli_path = cli_path
        self.voice_ref = voice_ref
        self.gaze_ms = gaze_ms
        self.aspect_ratio = aspect_ratio
        self.on_log = on_log or (lambda msg: print(f"[{self.slot.day:02d}_{self.slot.slot_id:02d}] {msg}"))

        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str) -> None:
        self.on_log(msg)

    def compose_scenes(self, script_scenes: list[dict]) -> list[Path]:
        """
        Dựng 4 scene với các hình khối nghệ thuật vẽ tay phù hợp kịch bản.
        """
        composed_paths = []
        for i in range(4):
            scene_id = f"scene_{i+1:02d}"
            src_img_path = self.base_images[i]
            img = Image.open(src_img_path).convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(img)
            cfg = script_scenes[i]

            if i == 0:
                # Cảnh 1: Cảnh báo sai lầm & Hook
                draw.rectangle((0, 0, 1080, 175), fill=PAPER_BG)
                draw.rectangle((0, 1710, 1080, 1920), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 35, 970, 155), fill=THEME_COLOR, text=cfg.get("title", self.slot.title), max_font_size=38)
                
                # Bong bóng đối thoại truyện tranh sinh động có đuôi chỉ thẳng vào nhân vật em bé
                balloon_bbox = (60, 175, 1020, 415)
                draw_speech_balloon(draw, balloon_bbox, fill=(255, 255, 255, 250), outline=RED_COLOR, width=3, tail_x=240, tail_y=465)
                
                alert_title = cfg.get("alert_title", "TUYỆT ĐỐI KHÔNG TRỘN NẾP & HẠT SEN!")
                alert_desc = f"{cfg.get('alert_bullet1', '')}\n{cfg.get('alert_bullet2', '')}".strip()
                draw_auto_card_text(
                    draw, balloon_bbox,
                    title=alert_title,
                    desc=alert_desc,
                    theme_color=RED_COLOR,
                    desc_color=(40, 40, 40),
                    max_title_font=30,
                    min_title_font=18,
                    max_desc_font=22,
                    min_desc_font=15,
                    align="center"
                )

                # Huy hiệu cảnh báo dạng viên nang (pill badge) tự ôm sát text, căn giữa chuẩn mực (y=435..495)
                warn_text = cfg.get("warn_label", "CẢNH BÁO Y KHOA: CẤM NẾP & HẠT SEN")
                pill_box = draw_warning_pill(draw, 540, 465, warn_text, icon="prohibit", theme_color=RED_COLOR, border_color=RED_COLOR)

                # Thẻ kết luận đáy trang: Cuộn sớ thư pháp sang trọng (y=1725..1875)
                bot_bbox = (60, 1725, 1020, 1875)
                draw_seamless_parchment(draw, bot_bbox, fill=(255, 250, 238), outline=THEME_COLOR, width=3)
                draw_auto_card_text(
                    draw, bot_bbox,
                    title=cfg.get("bot_title", "DẠ DÀY NON NỚT CỦA BÉ CHỈ CẦN GẠO TẺ NGUYÊN CÁM"),
                    desc=cfg.get("bot_desc", "Bảo vệ đường ruột và hệ tiêu hóa khỏe mạnh ngay từ ngày đầu"),
                    theme_color=THEME_COLOR,
                    desc_color=(70, 70, 70),
                    max_title_font=28,
                    min_title_font=16,
                    max_desc_font=20,
                    min_desc_font=14,
                    icon_left_pad=30,
                    icon_right_pad=30,
                    align="center"
                )

                elements = [
                    {"id": "s1_banner", "label": "Ruy Băng Tiêu Đề", "region": {"x": 40, "y": 25, "width": 1000, "height": 140}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s1_alert_box", "label": "Bong Bóng Thoại", "region": {"x": 50, "y": 165, "width": 980, "height": 260}, "reveal": {"startMs": 2000, "durationMs": 3500}},
                    {"id": "s1_prohibit_icon", "label": "Huy Hiệu Cấm", "region": {"x": max(0, pill_box[0] - 5), "y": max(0, pill_box[1] - 5), "width": (pill_box[2] - pill_box[0]) + 10, "height": (pill_box[3] - pill_box[1]) + 10}, "reveal": {"startMs": 5600, "durationMs": 1500}},
                    {"id": "s1_baby_visual", "label": "Hình Minh Họa", "region": {"x": 0, "y": 500, "width": 1080, "height": 1210}, "reveal": {"startMs": 7200, "durationMs": 5500}},
                    {"id": "s1_summary_card", "label": "Thẻ Kết Luận Đáy", "region": {"x": 50, "y": 1715, "width": 980, "height": 170}, "reveal": {"startMs": 12800, "durationMs": 2500}}
                ]

            elif i == 1:
                # Cảnh 2: Cơ chế y khoa
                draw.rectangle((0, 0, 1080, 150), fill=PAPER_BG)
                draw.rectangle((0, 880, 1080, 1060), fill=PAPER_BG)
                draw.rectangle((0, 1670, 1080, 1920), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 40, 970, 155), fill=THEME_COLOR, text=cfg.get("title", "TẠI SAO BÉ CHƯA THỂ ĂN GẠO NẾP?"), max_font_size=38)
                
                # Thẻ xanh (Dạ dày êm dịu): ĐÁM MÂY BỒNG BỀNH LIỀN KHỐI (Seamless Cloud)
                cloud_bbox = (50, 885, 1030, 1055)
                draw_seamless_cloud(draw, cloud_bbox, fill=(255, 255, 255, 252), outline=GREEN_COLOR, width=3)
                draw_auto_card_text(
                    draw, cloud_bbox,
                    title=cfg.get("good_title", "CHÁO GẠO TẺ RÂY 1:10 — HẤP THU ÊM DỊU"),
                    desc=cfg.get("good_desc", "Dạ dày 6 tháng chỉ bằng quả trứng, tiêu hóa nhẹ nhàng"),
                    theme_color=(39, 174, 96),
                    desc_color=(50, 50, 50),
                    max_title_font=30,
                    min_title_font=18,
                    max_desc_font=22,
                    min_desc_font=15,
                    align="center"
                )

                # Thẻ đỏ (Cảnh báo quá tải): TORN PAPER SCRAPBOOK VỚI GHIM BẤM 3D
                torn_bbox = (50, 1675, 1030, 1915)
                draw_torn_paper_card(draw, torn_bbox, fill=(255, 255, 255, 250), outline=RED_COLOR, pin_color=RED_COLOR)
                draw_auto_card_text(
                    draw, torn_bbox,
                    title=cfg.get("bad_title", "GẠO NẾP & HẠT SEN — QUÁ TẢI TIÊU HÓA"),
                    desc=cfg.get("bad_desc", "Đầy bụng, khó tiêu, lên men đường ruột khiến con quấy khóc"),
                    theme_color=RED_COLOR,
                    desc_color=(50, 50, 50),
                    max_title_font=30,
                    min_title_font=18,
                    max_desc_font=22,
                    min_desc_font=15,
                    align="center"
                )

                elements = [
                    {"id": "s2_banner", "label": "Ruy Băng Tiêu Đề", "region": {"x": 40, "y": 25, "width": 1000, "height": 140}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s2_stomach_visual", "label": "Dạ Dày Quả Trứng", "region": {"x": 0, "y": 160, "width": 1080, "height": 720}, "reveal": {"startMs": 2000, "durationMs": 4000}},
                    {"id": "s2_cloud_card", "label": "Đám Mây Tiêu Hóa", "region": {"x": 40, "y": 875, "width": 1000, "height": 190}, "reveal": {"startMs": 6100, "durationMs": 2500}},
                    {"id": "s2_grain_visual", "label": "Hạt Nếp & Hạt Sen", "region": {"x": 0, "y": 1070, "width": 1080, "height": 600}, "reveal": {"startMs": 8700, "durationMs": 4000}},
                    {"id": "s2_torn_card", "label": "Thẻ Cảnh Báo Mép Rách", "region": {"x": 40, "y": 1665, "width": 1000, "height": 245}, "reveal": {"startMs": 12800, "durationMs": 2500}}
                ]

            elif i == 2:
                # Cảnh 3: 3 Bước thực hành Tiêu chuẩn vàng
                draw.rectangle((0, 0, 1080, 150), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 40, 970, 155), fill=THEME_COLOR, text=cfg.get("title", "3 BƯỚC NẤU CHÁO RÂY 1:10 CHUẨN Y KHOA"), max_font_size=38)

                # Vẽ 3 thẻ chỉ dẫn nghệ thuật Washi Memo so le Zigzag chuẩn vùng trống (Negative Space)
                # Bước 1 (Hình bên trái x in [0, 520]): Thẻ đặt bên phải tại x=555 (x0=635..x1=1040, y=270)
                b1_box = draw_step_pill_badge(draw, 555, 270, "1", cfg.get("step1_title", "BƯỚC 1: GẠO TẺ NGUYÊN CÁM"), cfg.get("step1_desc", ["Vo nhẹ 1 lần với nước sạch", "Giữ trọn vitamin nhóm B"]), tag_text=cfg.get("step1_tag", "GẠO NGUYÊN CÁM"), theme_color=THEME_COLOR, card_width=405)
                # Bước 2 (Hình bên phải x in [560, 1080]): Thẻ đặt bên trái tại x=40 (x0=120..x1=540, y=870)
                b2_box = draw_step_pill_badge(draw, 40, 870, "2", cfg.get("step2_title", "BƯỚC 2: TỶ LỆ VÀNG 1:10"), cfg.get("step2_desc", ["10g gạo nấu cùng 100ml nước", "Ninh nhỏ lửa 45 phút"]), tag_text=cfg.get("step2_tag", "TỶ LỆ VÀNG 1:10"), theme_color=GREEN_COLOR, card_width=420)
                # Bước 3 (Hình bên trái x in [0, 580]): Thẻ đặt bên phải tại x=595 (x0=675..x1=1040, y=1440)
                b3_box = draw_step_pill_badge(draw, 595, 1440, "3", cfg.get("step3_title", "BƯỚC 3: RÂY MỊN ĐỒNG NHẤT"), cfg.get("step3_desc", ["Đổ qua rây 0.5mm khi còn ấm", "Miết nhẹ lưng thìa 2 lần"]), tag_text=cfg.get("step3_tag", "RÂY MỊN 0.5MM"), theme_color=BLUE_COLOR, card_width=365)

                elements = [
                    {"id": "s3_banner", "label": "Ruy Băng Tiêu Đề", "region": {"x": 40, "y": 25, "width": 1000, "height": 135}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s3_step1_visual", "label": "Hình Minh Họa Bước 1", "region": {"x": 0, "y": 150, "width": 1080, "height": 570}, "reveal": {"startMs": 2000, "durationMs": 3000}},
                    {"id": "s3_step1_card", "label": "Thẻ Bước 1 Phải", "region": {"x": max(0, b1_box[0] - 4), "y": max(0, b1_box[1] - 4), "width": (b1_box[2] - b1_box[0]) + 8, "height": (b1_box[3] - b1_box[1]) + 8}, "reveal": {"startMs": 5100, "durationMs": 2500}},
                    {"id": "s3_step2_visual", "label": "Hình Minh Họa Bước 2", "region": {"x": 0, "y": 720, "width": 1080, "height": 580}, "reveal": {"startMs": 7700, "durationMs": 3000}},
                    {"id": "s3_step2_card", "label": "Thẻ Bước 2 Trái", "region": {"x": max(0, b2_box[0] - 4), "y": max(0, b2_box[1] - 4), "width": (b2_box[2] - b2_box[0]) + 8, "height": (b2_box[3] - b2_box[1]) + 8}, "reveal": {"startMs": 10800, "durationMs": 2500}},
                    {"id": "s3_step3_visual", "label": "Hình Minh Họa Bước 3", "region": {"x": 0, "y": 1300, "width": 1080, "height": 620}, "reveal": {"startMs": 13400, "durationMs": 3000}},
                    {"id": "s3_step3_card", "label": "Thẻ Bước 3 Phải", "region": {"x": max(0, b3_box[0] - 4), "y": max(0, b3_box[1] - 4), "width": (b3_box[2] - b3_box[0]) + 8, "height": (b3_box[3] - b3_box[1]) + 8}, "reveal": {"startMs": 16500, "durationMs": 2500}}
                ]

            else:
                # Cảnh 4: Lời khuyên & CTA Thoáng Đãng
                draw.rectangle((0, 0, 1080, 150), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 40, 970, 155), fill=THEME_COLOR, text=cfg.get("title", "NGUYÊN TẮC VÀNG BỮA ĐẦU TIÊN"), max_font_size=38)

                # 3 Thẻ Lời khuyên Vạn năng (Universal Advice Cards) với số thứ tự tròn 1, 2, 3 và màu sắc chủ đề
                ac1_box = draw_advice_card(
                    draw, 540, 1130, "1",
                    title=cfg.get("badge1_label", "1 - 2 THÌA CÀ PHÊ NHỎ (5ML)"),
                    subtitle=cfg.get("badge1_desc", None),
                    theme_color=THEME_COLOR, card_w=920, card_h=92
                )
                ac2_box = draw_advice_card(
                    draw, 540, 1250, "2",
                    title=cfg.get("badge2_label", "ĂN CỮ SÁNG: 9H - 10H VUI VẺ"),
                    subtitle=cfg.get("badge2_desc", None),
                    theme_color=GREEN_COLOR, card_w=920, card_h=92
                )
                ac3_box = draw_advice_card(
                    draw, 540, 1370, "3",
                    title=cfg.get("badge3_label", "THEO DÕI PHÂN & DA 3 NGÀY"),
                    subtitle=cfg.get("badge3_desc", None),
                    theme_color=BLUE_COLOR, card_w=920, card_h=92
                )

                # CTA Capsule đặt ở khoảng y=1490..1640 (giải phóng hoàn toàn doodle trái tim & dâu tây ở y=1700..1820)
                cta_bbox = (60, 1500, 1020, 1650)
                draw_cta_capsule(draw, cta_bbox, title=cfg.get("cta_title", "BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!"), subtext=cfg.get("cta_sub", "Đồng hành chăm con khỏe mạnh chuẩn y khoa"), fill=THEME_COLOR)

                elements = [
                    {"id": "s4_banner", "label": "Ruy Băng Nguyên Tắc", "region": {"x": 40, "y": 25, "width": 1000, "height": 140}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s4_mom_feeding", "label": "Hình Mẹ Đút Bé", "region": {"x": 0, "y": 160, "width": 1080, "height": 950}, "reveal": {"startMs": 2000, "durationMs": 5000}},
                    {"id": "s4_icon_badges", "label": "3 Huy Hiệu Hướng Dẫn", "region": {"x": 50, "y": 1070, "width": 980, "height": 390}, "reveal": {"startMs": 7100, "durationMs": 3500}},
                    {"id": "s4_heart_cta", "label": "Khối Viên Nang Follow", "region": {"x": 50, "y": 1490, "width": 980, "height": 170}, "reveal": {"startMs": 10700, "durationMs": 2500}},
                    {"id": "s4_doodle_visual", "label": "Doodle Trái Tim & Dâu Tây", "region": {"x": 350, "y": 1680, "width": 400, "height": 170}, "reveal": {"startMs": 13300, "durationMs": 2000}}
                ]

            out_img = self.project_dir / f"{scene_id}.png"
            img.convert("RGB").save(out_img, quality=95)
            composed_paths.append(out_img)

            annotation = {
                "schemaVersion": 1,
                "canvas": {"width": 1080, "height": 1920},
                "background": {"color": "#F5EBD7"},
                "elements": elements
            }
            (self.project_dir / f"{scene_id}.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")

        return composed_paths

    def build_project_manifest(self, scripts_by_scene: list[str]) -> Path:
        """Tạo file project.json liên kết kịch bản 4 cảnh và các element."""
        scenes = [
            {"id": "scene_01", "title": "Cảnh 1: Cảnh báo", "image": "scene_01.png", "annotation": "scene_01.annotation.json"},
            {"id": "scene_02", "title": "Cảnh 2: Cơ chế", "image": "scene_02.png", "annotation": "scene_02.annotation.json"},
            {"id": "scene_03", "title": "Cảnh 3: 3 Bước", "image": "scene_03.png", "annotation": "scene_03.annotation.json"},
            {"id": "scene_04", "title": "Cảnh 4: Lời khuyên", "image": "scene_04.png", "annotation": "scene_04.annotation.json"}
        ]
        elements_map = [
            ["s1_banner", "s1_alert_box", "s1_prohibit_icon", "s1_baby_visual", "s1_summary_card"],
            ["s2_banner", "s2_stomach_visual", "s2_cloud_card", "s2_grain_visual", "s2_torn_card"],
            ["s3_banner", "s3_step1_visual", "s3_step1_card", "s3_step2_visual", "s3_step2_card", "s3_step3_visual", "s3_step3_card"],
            ["s4_banner", "s4_mom_feeding", "s4_icon_badges", "s4_heart_cta", "s4_doodle_visual"]
        ]

        narration = [
            {
                "id": f"cue_{i+1:02d}",
                "sceneId": f"scene_{i+1:02d}",
                "text": scripts_by_scene[i],
                "elementIds": elements_map[i],
                "pauseBeforeMs": 100
            }
            for i in range(4)
        ]

        manifest = {
            "schemaVersion": 1,
            "title": self.slot.title,
            "aspectRatio": self.aspect_ratio,
            "penBrand": "Ăn dặm mẹ Dâu",
            "scenes": scenes,
            "narration": narration
        }
        manifest_path = self.project_dir / "project.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest_path

    def run_pipeline(self, script_scenes_cfg: list[dict], scripts_text: list[str]) -> Optional[Path]:
        """Thực thi trọn vẹn quy trình tạo video theo Tiêu Chuẩn Vàng."""
        self.log("--- BƯỚC 1: DỰNG 4 CẢNH ĐỒ HỌA VẼ TAY NGHỆ THUẬT AUTO-FIT ---")
        self.compose_scenes(script_scenes_cfg)
        manifest_path = self.build_project_manifest(scripts_text)
        project = _read_manifest(manifest_path)

        self.log("--- BƯỚC 2: TẠO GIỌNG ĐỌC XUÂN DUNG THEO TỪNG CẢNH (OMNIVOICE) ---")
        scene_audio_map = generate_scene_voices(
            cli_path=self.cli_path,
            project=project,
            reference_audio=self.voice_ref,
            output_dir=self.audio_dir,
            on_log=lambda msg: self.log(f"[OmniVoice] {msg}"),
            cancel_event=threading.Event(),
            reference_text="Muốn đổi món với thịt bò cho bé, đây là 5 gợi ý dễ ăn."
        )

        self.log(f"--- BƯỚC 3: BIÊN DỊCH TIMELINE & ĐỒNG BỘ NÉT VẼ (GAZE {self.gaze_ms}MS) ---")
        timeline_res = compile_scene_timeline(
            project=project,
            scene_audio=scene_audio_map,
            output_dir=self.output_dir,
            on_log=lambda m: None,
            gaze_ms=self.gaze_ms
        )
        project.voice = timeline_res.voice_path
        project.runtime_annotations = timeline_res.runtime_annotations
        duration_s = timeline_res.total_duration_ms / 1000
        self.log(f"Thời lượng video chuẩn xác: {duration_s:.1f}s")

        self.log(f"--- BƯỚC 4: RENDER VIDEO GPU VÀ GHÉP TRANSITION SLIDELEFT ({self.aspect_ratio}) ---")
        commands, final_target = build_commands(
            project=project,
            output_dir=self.output_dir,
            aspect_ratio=self.aspect_ratio
        )

        env = subprocess_environment()
        for cmd_idx, cmd in enumerate(commands, start=1):
            self.log(f"[{cmd_idx}/{len(commands)}] {cmd.label}...")
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
                self.log(f"LỖI TẠI BƯỚC {cmd.label}: {proc.stderr[:400]}")
                return None

        final_mp4 = self.output_dir / "final.mp4"
        if not final_mp4.is_file():
            self.log("Không tìm thấy file final.mp4 sau khi render!")
            return None

        # Xuất sang Google Drive
        dest_filename = f"Day_{self.slot.day:02d}_Slot_{self.slot.slot_id:02d}_{self.slot.title.replace(' ', '_').replace('?', '').replace('!', '')}_2K.mp4"
        dest_path = DRIVE_OUTPUT_DIR / dest_filename
        DRIVE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_mp4, dest_path)
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        self.log(f"🎉 ĐÃ XUẤT BẢN THÀNH CÔNG SANG GOOGLE DRIVE: {dest_path} ({size_mb:.2f} MB, {duration_s:.1f}s)")

        # Cập nhật Sheets Webhook
        try:
            payload = {
                "action": "update_row",
                "day": self.slot.day,
                "slot_id": self.slot.slot_id,
                "video_path": str(dest_path),
                "status": f"READY_TO_PUBLISH (2K 1440x2560 - {duration_s:.1f}s)"
            }
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.log(f"Google Sheets Webhook Sync: {resp.read().decode('utf-8')}")
        except Exception as ex:
            self.log(f"Google Sheets Sync Warning: {ex}")

        return dest_path
