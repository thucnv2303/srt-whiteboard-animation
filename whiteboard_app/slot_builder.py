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
                draw.rectangle((0, 1750, 1080, 1920), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 35, 970, 155), fill=THEME_COLOR, text=cfg.get("title", self.slot.title), max_font_size=38)
                
                # Comic Bubble gọn gàng trong khoảng y=175..410, không có đuôi chọc vào chữ
                draw.rounded_rectangle((70, 175, 1010, 410), radius=24, fill=(255, 255, 255, 248), outline=RED_COLOR, width=3)
                f_alert_head = get_font(FONT_BOLD, 33)
                f_alert_body = get_font(FONT_BOLD, 26)
                draw.text((540, 220), cfg.get("alert_title", "TUYỆT ĐỐI KHÔNG TRỘN NẾP & HẠT SEN!"), font=f_alert_head, fill=RED_COLOR, anchor="mm")
                draw.text((540, 280), cfg.get("alert_bullet1", "• Bé 6 tháng chưa có men tiêu hóa tinh bột dẻo"), font=f_alert_body, fill=(40, 40, 40), anchor="mm")
                draw.text((540, 340), cfg.get("alert_bullet2", "• Gây trướng bụng, đầy hơi, nôn trớ & sợ ăn dặm"), font=f_alert_body, fill=(185, 28, 28), anchor="mm")

                # Huy hiệu cảnh báo dạng thẻ pill nằm ngang thoáng đãng (y=430..485) - nằm trên đỉnh đầu bé an toàn
                warn_text = cfg.get("warn_label", "CẢNH BÁO Y KHOA: CẤM NẾP & HẠT SEN")
                f_warn = get_font(FONT_BOLD, 22)
                bb_w = draw.textbbox((0, 0), warn_text, font=f_warn)
                txt_w = bb_w[2] - bb_w[0]
                pill_w = txt_w + 80
                pill_x0 = 540 - pill_w // 2
                pill_x1 = 540 + pill_w // 2
                draw.rounded_rectangle((pill_x0, 430, pill_x1, 485), radius=16, fill=(255, 245, 245), outline=RED_COLOR, width=2)
                draw_prohibition_badge(draw, pill_x0 + 26, 457, radius=16)
                draw.text((pill_x0 + 52, 457), warn_text, font=f_warn, fill=RED_COLOR, anchor="lm")

                # Thẻ kết luận đáy trang (y=1760..1880) - giải phóng hoàn toàn khoảng giữa
                draw.rounded_rectangle((60, 1760, 1020, 1880), radius=20, fill=(255, 243, 224), outline=THEME_COLOR, width=2)
                f_bot1 = get_font(FONT_BOLD, 30)
                f_bot2 = get_font(FONT_BOLD, 24)
                draw.text((540, 1800), cfg.get("bot_title", "DẠ DÀY NON NỚT CỦA BÉ CHỈ CẦN GẠO TẺ NGUYÊN CÁM"), font=f_bot1, fill=THEME_COLOR, anchor="mm")
                draw.text((540, 1845), cfg.get("bot_desc", "Bảo vệ đường ruột và hệ tiêu hóa khỏe mạnh ngay từ ngày đầu"), font=f_bot2, fill=(60, 60, 60), anchor="mm")

                elements = [
                    {"id": "s1_banner", "label": "Ruy Băng Tiêu Đề", "region": {"x": 40, "y": 25, "width": 1000, "height": 140}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s1_alert_box", "label": "Bong Bóng Thoại", "region": {"x": 50, "y": 165, "width": 980, "height": 255}, "reveal": {"startMs": 2000, "durationMs": 3500}},
                    {"id": "s1_prohibit_icon", "label": "Huy Hiệu Cấm", "region": {"x": 150, "y": 425, "width": 780, "height": 70}, "reveal": {"startMs": 5600, "durationMs": 1500}},
                    {"id": "s1_baby_visual", "label": "Hình Minh Họa", "region": {"x": 0, "y": 500, "width": 1080, "height": 1250}, "reveal": {"startMs": 7200, "durationMs": 5500}},
                    {"id": "s1_summary_card", "label": "Thẻ Kết Luận Đáy", "region": {"x": 50, "y": 1750, "width": 980, "height": 140}, "reveal": {"startMs": 12800, "durationMs": 2500}}
                ]

            elif i == 1:
                # Cảnh 2: Cơ chế y khoa
                draw.rectangle((0, 0, 1080, 150), fill=PAPER_BG)
                draw.rectangle((0, 890, 1080, 1060), fill=PAPER_BG)
                draw.rectangle((0, 1680, 1080, 1920), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 40, 970, 155), fill=THEME_COLOR, text=cfg.get("title", "TẠI SAO BÉ CHƯA THỂ ĂN GẠO NẾP?"), max_font_size=38)
                
                # Thẻ Washi xanh ở khoảng giữa thoáng đãng (y=900..1035)
                draw_washi_memo_card(draw, (60, 900, 1020, 1035), fill=(255, 255, 255, 248), outline=GREEN_COLOR, tape_color=(120, 220, 160))
                f_label = get_font(FONT_BOLD, 34)
                f_sub = get_font(FONT_BOLD, 26)
                draw.text((540, 942), cfg.get("good_title", "CHÁO GẠO TẺ RÂY 1:10 — HẤP THU ÊM DỊU"), font=f_label, fill=(39, 174, 96), anchor="mm")
                draw.text((540, 990), cfg.get("good_desc", "Dạ dày 6 tháng chỉ bằng quả trứng, tiêu hóa nhẹ nhàng"), font=f_sub, fill=(50, 50, 50), anchor="mm")

                # Thẻ Washi đỏ ở khoảng đáy thoáng đãng (y=1690..1845)
                draw_washi_memo_card(draw, (60, 1690, 1020, 1845), fill=(255, 255, 255, 248), outline=RED_COLOR, tape_color=(250, 160, 150))
                draw.text((540, 1735), cfg.get("bad_title", "GẠO NẾP & HẠT SEN — GÂY QUÁ TẢI TIÊU HÓA!"), font=f_label, fill=RED_COLOR, anchor="mm")
                draw.text((540, 1788), cfg.get("bad_desc", "Thiếu men amylase phân giải, thức ăn ứ đọng sinh đầy hơi"), font=f_sub, fill=(185, 28, 28), anchor="mm")

                elements = [
                    {"id": "s2_banner", "label": "Ruy Băng Cơ Chế", "region": {"x": 40, "y": 25, "width": 1000, "height": 140}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s2_happy_visual", "label": "Hình Dạ Dày Êm Dịu", "region": {"x": 0, "y": 170, "width": 1080, "height": 720}, "reveal": {"startMs": 2000, "durationMs": 4000}},
                    {"id": "s2_happy_card", "label": "Thẻ Xanh Dễ Tiêu", "region": {"x": 50, "y": 890, "width": 980, "height": 160}, "reveal": {"startMs": 6100, "durationMs": 2500}},
                    {"id": "s2_stressed_visual", "label": "Hình Dạ Dày Quá Tải", "region": {"x": 0, "y": 1060, "width": 1080, "height": 620}, "reveal": {"startMs": 8700, "durationMs": 4000}},
                    {"id": "s2_stressed_card", "label": "Thẻ Đỏ Quá Tải", "region": {"x": 50, "y": 1680, "width": 980, "height": 180}, "reveal": {"startMs": 12800, "durationMs": 2500}}
                ]

            elif i == 2:
                # Cảnh 3: 3 Bước Thực Hành So Le Zigzag
                draw.rectangle((0, 0, 1080, 145), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 35, 970, 150), fill=THEME_COLOR, text=cfg.get("title", "CÔNG THỨC CHÁO RÂY 1:10 CHUẨN Y KHOA"), max_font_size=38)

                # BƯỚC 1: Đặt so le bên phải (x=500..1020, y=220..395), né bao gạo bên trái
                draw_step_pill_badge(draw, 490, 220, "1", cfg.get("step1_title", "GẠO NGUYÊN CÁM"), cfg.get("step1_desc", ["Chọn gạo thơm mới", "Vo nhẹ 1 lần giữ vitamin B1"]), tag_text="VITAMIN B1", theme_color=THEME_COLOR, card_width=440)

                # BƯỚC 2: Đặt so le bên trái (x=50..580, y=780..955), né nồi cháo bên phải
                draw_step_pill_badge(draw, 50, 780, "2", cfg.get("step2_title", "TỶ LỆ VÀNG 1 : 10"), cfg.get("step2_desc", ["10g gạo + 100ml nước", "Ninh nhỏ lửa 45 phút"]), tag_text="NINH 45 PHÚT", theme_color=THEME_COLOR, card_width=440)

                # BƯỚC 3: Đặt so le bên phải (x=510..1030, y=1420..1595), né rây cháo bên trái (max_x=470)
                draw_step_pill_badge(draw, 510, 1420, "3", cfg.get("step3_title", "RÂY MỊN KHI ẤM"), cfg.get("step3_desc", ["Rây qua lưới 0.5mm", "Miết lưng thìa lấy cháo sánh"]), tag_text="LƯỚI 0.5MM", theme_color=THEME_COLOR, card_width=430)

                elements = [
                    {"id": "s3_banner", "label": "Ruy Băng Tiêu Đề", "region": {"x": 40, "y": 25, "width": 1000, "height": 135}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s3_step1_visual", "label": "Hình Bao Gạo", "region": {"x": 50, "y": 170, "width": 440, "height": 550}, "reveal": {"startMs": 2000, "durationMs": 3000}},
                    {"id": "s3_step1_card", "label": "Thẻ Bước 1 Phải", "region": {"x": 490, "y": 210, "width": 540, "height": 200}, "reveal": {"startMs": 5100, "durationMs": 2500}},
                    {"id": "s3_step2_visual", "label": "Hình Nồi Ninh", "region": {"x": 520, "y": 720, "width": 520, "height": 550}, "reveal": {"startMs": 7700, "durationMs": 3000}},
                    {"id": "s3_step2_card", "label": "Thẻ Bước 2 Trái", "region": {"x": 40, "y": 770, "width": 480, "height": 200}, "reveal": {"startMs": 10800, "durationMs": 2500}},
                    {"id": "s3_step3_visual", "label": "Hình Rây Cháo", "region": {"x": 50, "y": 1300, "width": 480, "height": 580}, "reveal": {"startMs": 13400, "durationMs": 3000}},
                    {"id": "s3_step3_card", "label": "Thẻ Bước 3 Phải", "region": {"x": 530, "y": 1410, "width": 500, "height": 200}, "reveal": {"startMs": 16500, "durationMs": 2500}}
                ]

            else:
                # Cảnh 4: Lời khuyên & CTA Thoáng Đãng
                draw.rectangle((0, 0, 1080, 150), fill=PAPER_BG)
                draw_ribbon_banner(draw, (110, 40, 970, 155), fill=THEME_COLOR, text=cfg.get("title", "NGUYÊN TẮC VÀNG BỮA ĐẦU TIÊN"), max_font_size=38)

                # 3 Huy hiệu xếp tầng gọn gàng ở khoảng trống (y=1100..1440)
                draw_spoon_dosage(draw, 540, 1130, label=cfg.get("badge1_label", "1 - 2 THÌA CÀ PHÊ NHỎ (5ML)"))
                draw_sun_time_badge(draw, 540, 1250, label=cfg.get("badge2_label", "ĂN CỮ SÁNG: 9H - 10H VUI VẺ"))
                draw_calendar_allergy_badge(draw, 540, 1370, label=cfg.get("badge3_label", "THEO DÕI PHÂN & DA 3 NGÀY"))

                # CTA Capsule đặt ở khoảng y=1490..1640 (giải phóng hoàn toàn doodle trái tim & dâu tây ở y=1700..1820)
                cta_bbox = (60, 1500, 1020, 1650)
                draw_cta_capsule(draw, cta_bbox, title=cfg.get("cta_title", "BẤM FOLLOW ĂN DẶM MẸ DÂU NGAY!"), subtext=cfg.get("cta_sub", "Đồng hành chăm con khỏe mạnh chuẩn y khoa"), fill=THEME_COLOR)

                elements = [
                    {"id": "s4_banner", "label": "Ruy Băng Nguyên Tắc", "region": {"x": 40, "y": 25, "width": 1000, "height": 140}, "reveal": {"startMs": 100, "durationMs": 1800}},
                    {"id": "s4_mom_feeding", "label": "Hình Mẹ Đút Bé", "region": {"x": 0, "y": 160, "width": 1080, "height": 950}, "reveal": {"startMs": 2000, "durationMs": 5000}},
                    {"id": "s4_icon_badges", "label": "3 Huy Hiệu Hướng Dẫn", "region": {"x": 60, "y": 1080, "width": 960, "height": 380}, "reveal": {"startMs": 7100, "durationMs": 3500}},
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
            ["s2_banner", "s2_happy_visual", "s2_happy_card", "s2_stressed_visual", "s2_stressed_card"],
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
