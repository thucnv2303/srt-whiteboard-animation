#!/usr/bin/env python3
"""
Telegram Daily Trigger & Confirmation Bot for Whiteboard Animation App.
Kênh: "Ăn dặm mẹ Dâu"

Tự động hóa:
1. Gửi thông báo kịch bản video hàng ngày lên Telegram.
2. Hiển thị 2 nút bấm Inline: [✅ Duyệt & Tạo Video] và [❌ Bỏ qua / Sửa sau].
3. Lắng nghe xác nhận (Polling): CHỈ KHI người dùng bấm Duyệt trên Telegram thì mới kích hoạt render video.
4. Báo cáo tiến độ và gửi thông báo hoàn tất MP4 về Telegram.

Sử dụng thư viện chuẩn của Python (urllib.request, json, time, threading) - không cần cài thêm package.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

# Đảm bảo import được module từ thư mục gốc
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from whiteboard_app.jobs import (
    COMPLETED,
    FAILED,
    WAITING,
    JobResult,
    JobStore,
    SequentialJobRunner,
)
from whiteboard_app.project import VideoProject, load_project
from whiteboard_app.renderer import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TelegramTrigger")


class TelegramBotClient:
    def __init__(self, token: str, default_chat_id: str = "") -> None:
        self.token = token.strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.default_chat_id = default_chat_id.strip()

    def _api_call(self, endpoint: str, data: dict | None = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        payload = json.dumps(data or {}).encode("utf-8") if data is not None else None
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"} if payload else {},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.error("Lỗi gọi Telegram API (%s): %s", endpoint, exc)
            return {"ok": False, "description": str(exc)}

    def get_me(self) -> dict:
        return self._api_call("getMe")

    def send_message(
        self,
        text: str,
        chat_id: str | None = None,
        reply_markup: dict | None = None,
        parse_mode: str = "Markdown",
    ) -> dict:
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            raise ValueError("Chưa cấu hình Chat ID nhận tin nhắn Telegram!")
        data = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._api_call("sendMessage", data)

    def answer_callback_query(self, callback_query_id: str, text: str = "") -> dict:
        return self._api_call(
            "answerCallbackQuery",
            {"callback_query_id": callback_query_id, "text": text},
        )

    def send_video(
        self,
        video_path: Path,
        caption: str = "",
        chat_id: str | None = None,
    ) -> dict:
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            return {"ok": False, "description": "Thiếu chat_id"}
        if not video_path.exists():
            return {"ok": False, "description": f"Không tìm thấy file video: {video_path}"}

        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
        url = f"{self.base_url}/sendVideo"

        body = []
        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{target_chat}\r\n'.encode("utf-8"))

        if caption:
            body.append(f"--{boundary}\r\n".encode("utf-8"))
            body.append(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode("utf-8"))

        body.append(f"--{boundary}\r\n".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="video"; filename="{video_path.name}"\r\n'.encode("utf-8"))
        body.append(b"Content-Type: video/mp4\r\n\r\n")
        body.append(video_path.read_bytes())
        body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

        payload = b"".join(body)
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.error("Lỗi gửi video sang Telegram: %s", exc)
            return {"ok": False, "description": str(exc)}

    def get_updates(self, offset: int = 0, timeout: int = 20) -> dict:
        return self._api_call("getUpdates", {"offset": offset, "timeout": timeout})


class DailyContentTrigger:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = (
            config_path or ROOT_DIR / "config" / "telegram_config.json"
        )
        self.config = self._load_config()
        self.bot = TelegramBotClient(
            token=self.config.get("bot_token", ""),
            default_chat_id=self.config.get("chat_id", ""),
        )
        dataset_300 = ROOT_DIR / "knowledge" / "an_dam_me_dau" / "CONTENT_PLAN_30_DAYS_300_VIDEOS.json"
        dataset_60 = ROOT_DIR / "knowledge" / "an_dam_me_dau" / "CONTENT_PLAN_30_DAYS_60_VIDEOS.json"
        self.dataset_path = dataset_300 if dataset_300.exists() else dataset_60
        self.store = JobStore()
        self.runner = SequentialJobRunner(self.store, on_event=self._on_runner_event)
        self.offset = 0
        self._running = True

    def _load_config(self) -> dict:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Không thể đọc %s: %s. Dùng mẫu mặc định.", self.config_path, exc)
        return {
            "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
            "daily_schedule_morning": "07:00",
            "daily_schedule_evening": "19:00",
            "pen_brand": "Ăn dặm mẹ Dâu",
            "default_aspect_ratio": "9:16",
        }

    def _load_dataset(self) -> list[dict]:
        if not self.dataset_path.exists():
            logger.error("Không tìm thấy file dữ liệu 60 video: %s", self.dataset_path)
            return []
        return json.loads(self.dataset_path.read_text(encoding="utf-8"))

    def send_daily_proposals(self, target_day: int | None = None) -> None:
        """Gửi 2 video của ngày được chọn (hoặc ngày hôm nay) lên Telegram."""
        dataset = self._load_dataset()
        if not dataset:
            return

        if target_day is None:
            # Lấy ngày theo chu kỳ 30 ngày trong tháng
            now = datetime.now()
            target_day = (now.day % 30) or 30

        items = [item for item in dataset if item.get("day") == target_day]
        if not items:
            logger.warning("Không tìm thấy video nào cho Ngày %s", target_day)
            return

        logger.info("Đang gửi %s đề xuất video Ngày %s sang Telegram...", len(items), target_day)
        for index, item in enumerate(items, 1):
            slot = item.get("slot", "")
            title = item.get("title", "")
            pillar = item.get("pillar", "")
            hook = item.get("hook", "")
            body = item.get("body", "")
            cta = item.get("cta", "")
            tiktok_caption = item.get("tiktok_caption", "")

            msg = (
                f"🍓 *[ĂN DẶM MẸ DÂU] — KẾ HOẠCH VIDEO NGÀY {target_day}*\n"
                f"⏰ *Khung giờ:* {slot}\n"
                f"📌 *Chủ đề:* {pillar}\n"
                f"🎬 *Tiêu đề:* *{title}*\n\n"
                f"🎯 *Hook (Mở đầu):*\n_{hook}_\n\n"
                f"📝 *Thân bài:* {body}\n\n"
                f"📣 *CTA:* _{cta}_\n\n"
                f"📱 *Caption TikTok:*\n`{tiktok_caption[:140]}...`\n\n"
                f"⚠️ *Xác nhận:* Bấm nút bên dưới để App Desktop bắt đầu dựng video này:"
            )

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "✅ Duyệt & Tạo Video Ngay",
                            "callback_data": f"APPROVE_DAY_{target_day}_SLOT_{index}",
                        },
                        {
                            "text": "❌ Bỏ qua / Sửa sau",
                            "callback_data": f"REJECT_DAY_{target_day}_SLOT_{index}",
                        },
                    ]
                ]
            }

            res = self.bot.send_message(msg, reply_markup=keyboard)
            if res.get("ok"):
                logger.info("Đã gửi video '%s' thành công!", title)
            else:
                logger.error("Lỗi gửi video '%s': %s", title, res.get("description"))
            time.sleep(1)

    def handle_callback(self, callback: dict) -> None:
        callback_id = callback.get("id", "")
        data = str(callback.get("data", ""))
        from_user = callback.get("from", {}).get("first_name", "User")
        message = callback.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))

        logger.info("Nhận callback từ %s: %s", from_user, data)

        if data.startswith("APPROVE_"):
            day_num = 1
            slot_index = 1
            if "DAY_" in data and "SLOT_" in data:
                parts = data.split("_")
                day_num = int(parts[2])
                slot_index = int(parts[4])
            elif "ROW_" in data and "DAY_" in data:
                parts = data.split("_")
                row_num = int(parts[2])
                day_num = int(parts[4])
                # Tính slot index từ row number (10 slot mỗi ngày)
                slot_index = ((row_num - 2) % 10) + 1 if row_num >= 2 else 1

            self.bot.answer_callback_query(
                callback_id, text="Đã nhận lệnh! Bắt đầu dựng video..."
            )
            self.bot.send_message(
                f"⏳ *ĐÃ XÁC NHẬN DUYỆT BỞI {from_user}!* \n"
                f"App Desktop đang chuẩn bị gói dự án và khởi động render cho Ngày {day_num} (Slot {slot_index})...",
                chat_id=chat_id,
            )

            # Khởi chạy pipeline render video
            self._execute_video_generation(day_num, slot_index, chat_id)

        elif data.startswith("REJECT_"):
            self.bot.answer_callback_query(
                callback_id, text="Đã bỏ qua video này."
            )
            self.bot.send_message(
                f"❌ *ĐÃ HỦY:* Video này đã được bỏ qua theo yêu cầu.",
                chat_id=chat_id,
            )

    def _execute_video_generation(self, day_num: int, slot_index: int, chat_id: str) -> None:
        """Tạo gói dự án và điều phối render."""
        dataset = self._load_dataset()
        items = [item for item in dataset if item.get("day") == day_num]
        if not items or slot_index > len(items):
            self.bot.send_message(f"❌ Không tìm thấy dữ liệu kịch bản Ngày {day_num}", chat_id=chat_id)
            return

        item = items[slot_index - 1]
        title = item.get("title", f"Video Ngày {day_num}")
        hook = item.get("hook", "")
        body = item.get("body", "")
        cta = item.get("cta", "")
        full_text = f"{hook} {body} {cta}".strip()

        # Tạo thư mục dự án cho video này
        run_dir = ROOT_DIR / "output" / "telegram_runs" / f"day_{day_num:02d}_slot_{slot_index}"
        run_dir.mkdir(parents=True, exist_ok=True)
        scenes_dir = run_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        # Ghi script.txt
        (run_dir / "script.txt").write_text(full_text, encoding="utf-8")

        # Chuẩn bị project.json
        project_data = {
            "schemaVersion": 1,
            "title": title,
            "version": 1,
            "aspectRatio": self.config.get("default_aspect_ratio", "9:16"),
            "script": "script.txt",
            "penBrand": self.config.get("pen_brand", "Ăn dặm mẹ Dâu"),
            "scenes": [
                {
                    "id": "scene-01",
                    "title": title,
                    "image": "scenes/scene-01.png",
                    "annotation": "scenes/scene-01.annotation.json",
                }
            ],
        }

        # Nếu chưa có ảnh thật, copy ảnh mẫu hoặc tạo ảnh giả lập để pipeline chạy
        sample_img = ROOT_DIR / "examples" / "beef-5-dishes" / "scene-01-realistic.webp"
        sample_annot = ROOT_DIR / "examples" / "beef-5-dishes" / "scene-01-realistic.annotation.json"
        
        target_img = scenes_dir / "scene-01.png"
        target_annot = scenes_dir / "scene-01.annotation.json"
        
        if sample_img.exists() and not target_img.exists():
            target_img.write_bytes(sample_img.read_bytes())
        if sample_annot.exists() and not target_annot.exists():
            target_annot.write_text(sample_annot.read_text(encoding="utf-8"), encoding="utf-8")

        manifest_path = run_dir / "project.json"
        manifest_path.write_text(json.dumps(project_data, ensure_ascii=False, indent=2), encoding="utf-8")

        self.bot.send_message(
            f"📦 *ĐÃ TẠO GÓI DỰ ÁN THÀNH CÔNG!*\n"
            f"🎬 Tiêu đề: *{title}*\n"
            f"🎨 *ĐANG BẮT ĐẦU DỰNG NÉT VẼ TAY & XUẤT MP4 9:16...*\n"
            f"⏳ Quá trình vẽ và xuất video mất khoảng 1 phút. Sau khi xong bot sẽ gửi video ngay vào đây cho bạn!",
            chat_id=chat_id,
        )

        def _async_render_and_send() -> None:
            try:
                project = load_project(manifest_path)
                cancel_event = threading.Event()
                output_render_dir = run_dir / "output"
                output_render_dir.mkdir(parents=True, exist_ok=True)

                def _on_log(msg: str) -> None:
                    logger.info("[%s] %s", title, msg)

                aspect_ratio = self.config.get("default_aspect_ratio", "9:16")
                result_video = run_pipeline(
                    project,
                    output_render_dir,
                    _on_log,
                    cancel_event,
                    aspect_ratio=aspect_ratio,
                )

                self.bot.send_message(
                    f"🎉 *RENDER THÀNH CÔNG!*\n"
                    f"🎬 Video: *{title}*\n"
                    f"📁 File: `{result_video}`\n"
                    f"Đang tải video thành phẩm lên Telegram...",
                    chat_id=chat_id,
                )

                # Gửi file video trực tiếp về Telegram
                self.bot.send_video(
                    result_video,
                    caption=f"🍓 Ăn Dặm Mẹ Dâu - {title}\n#andammeDau #andam #thucdonchobe",
                    chat_id=chat_id,
                )
                logger.info("Đã hoàn tất và gửi video '%s' về Telegram!", title)
            except Exception as exc:
                logger.error("Lỗi khi render tự động video '%s': %s", title, exc)
                self.bot.send_message(
                    f"❌ *Lỗi khi dựng video:* {exc}\nBạn có thể mở thư mục `{run_dir}` trên App Desktop để kiểm tra.",
                    chat_id=chat_id,
                )

        render_thread = threading.Thread(
            target=_async_render_and_send,
            name=f"render-day-{day_num}-slot-{slot_index}",
            daemon=True,
        )
        render_thread.start()

    def _on_runner_event(self, kind: str, job_id: str, payload: object) -> None:
        logger.info("Runner event: %s - Job: %s - Payload: %s", kind, job_id, payload)

    def start_polling(self) -> None:
        """Lắng nghe tương tác nút bấm từ người dùng trên Telegram."""
        logger.info("Bot đang lắng nghe xác nhận từ Telegram (Nhấn Ctrl+C để dừng)...")
        while self._running:
            try:
                updates = self.bot.get_updates(offset=self.offset, timeout=10)
                if updates.get("ok"):
                    for item in updates.get("result", []):
                        self.offset = item.get("update_id", 0) + 1
                        if "callback_query" in item:
                            self.handle_callback(item["callback_query"])
            except KeyboardInterrupt:
                logger.info("Đã dừng bot.")
                break
            except Exception as exc:
                logger.error("Lỗi trong vòng lặp polling: %s", exc)
                time.sleep(3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ăn Dặm Mẹ Dâu - Telegram Trigger Bot")
    parser.add_argument("--mode", choices=["listen", "send", "test"], default="listen", help="Chế độ chạy")
    parser.add_argument("--day", type=int, default=None, help="Số ngày (1-30) muốn gửi thông báo")
    parser.add_argument("--config", type=str, default=None, help="Đường dẫn file cấu hình json")

    args = parser.parse_args()
    config_path = Path(args.config) if args.config else None
    trigger = DailyContentTrigger(config_path)

    if args.mode == "test":
        me = trigger.bot.get_me()
        if me.get("ok"):
            print(f"✅ Kết nối Telegram thành công! Bot: @{me['result']['username']}")
        else:
            print(f"❌ Lỗi kết nối Telegram: {me.get('description')}")
    elif args.mode == "send":
        trigger.send_daily_proposals(target_day=args.day)
    elif args.mode == "listen":
        if args.day:
            trigger.send_daily_proposals(target_day=args.day)
        trigger.start_polling()


if __name__ == "__main__":
    main()
