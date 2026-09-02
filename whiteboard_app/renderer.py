from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .project import VideoProject


class RenderError(RuntimeError):
    """Lỗi render có nội dung phù hợp để hiển thị trên UI."""


@dataclass(frozen=True)
class RenderCommand:
    label: str
    argv: list[str]


@dataclass(frozen=True)
class AspectRatio:
    width: int
    height: int


ASPECT_RATIOS: dict[str, AspectRatio] = {
    "16:9": AspectRatio(1280, 720),
    "9:16": AspectRatio(1080, 1920),
    "1:1": AspectRatio(1080, 1080),
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def subprocess_environment() -> dict[str, str]:
    """Bắt tiến trình Python con dùng UTF-8 trên mọi cấu hình Windows."""
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    return environment


def build_commands(
    project: VideoProject,
    output_dir: Path,
    python_executable: str | None = None,
    aspect_ratio: str = "16:9",
) -> tuple[list[RenderCommand], Path]:
    if aspect_ratio not in ASPECT_RATIOS:
        raise RenderError(f"Tỷ lệ video chưa được hỗ trợ: {aspect_ratio}")
    repo = repository_root()
    python = python_executable or sys.executable
    renderer = repo / "scripts" / "render_stream_whiteboard.py"
    merger = repo / "scripts" / "merge_scenes.py"
    hand = repo / "assets" / "drawing-hand.png"
    for required in (renderer, merger, hand):
        if not required.exists():
            raise RenderError(f"Thiếu thành phần renderer: {required}")

    output_dir = output_dir.resolve()
    scene_dir = output_dir / "scenes"
    commands: list[RenderCommand] = []
    scene_outputs: list[Path] = []
    for index, scene in enumerate(project.scenes, start=1):
        scene_output = scene_dir / f"{index:02d}-{scene.scene_id}.mp4"
        scene_outputs.append(scene_output)
        annotation = project.runtime_annotations.get(scene.scene_id, scene.annotation)
        scene_argv = [
            python,
            str(renderer),
            str(scene.image),
            str(annotation),
            str(scene_output),
            str(hand),
            "--ink-path",
            "grid",
            "--color-fill",
            "contour-wipe",
        ]
        if project.pen_brand:
            scene_argv.extend(["--pen-brand", project.pen_brand])
        commands.append(
            RenderCommand(
                label=f"Dựng cảnh {index}/{len(project.scenes)} — {scene.title}",
                argv=scene_argv,
            )
        )

    final_output = output_dir / "final.mp4"
    needs_format = aspect_ratio != "16:9"
    if project.voice:
        merged_output = output_dir / "final-silent.mp4"
    elif needs_format:
        merged_output = output_dir / "final-source.mp4"
    else:
        merged_output = final_output
    commands.append(
        RenderCommand(
            label="Ghép các cảnh",
            argv=[
                python,
                str(merger),
                "--inputs",
                *[str(path) for path in scene_outputs],
                "--output",
                str(merged_output),
            ],
        )
    )
    media_for_format = merged_output
    if project.voice:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RenderError(
                "Dự án có voice nhưng máy chưa tìm thấy FFmpeg trong PATH. "
                "Hãy cài FFmpeg rồi mở lại app."
            )
        voiced_output = output_dir / ("final-source.mp4" if needs_format else "final.mp4")
        commands.append(
            RenderCommand(
                label="Gắn voice vào video",
                argv=[
                    ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(merged_output),
                    "-i",
                    str(project.voice),
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-af",
                    "apad",
                    "-shortest",
                    str(voiced_output),
                ],
            )
        )
        media_for_format = voiced_output
    if needs_format:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RenderError(
                "Tỷ lệ đã chọn cần FFmpeg nhưng máy chưa tìm thấy FFmpeg trong PATH."
            )
        spec = ASPECT_RATIOS[aspect_ratio]
        video_filter = (
            f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=increase,"
            f"crop={spec.width}:{spec.height}"
        )
        commands.append(
            RenderCommand(
                label=f"Định dạng video {aspect_ratio} — {spec.width}×{spec.height}",
                argv=[
                    ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(media_for_format),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a?",
                    "-vf",
                    video_filter,
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-movflags",
                    "+faststart",
                    str(final_output),
                ],
            )
        )
    return commands, final_output


def run_pipeline(
    project: VideoProject,
    output_dir: Path,
    on_log: Callable[[str], None],
    cancel_event: threading.Event | None = None,
    aspect_ratio: str = "16:9",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scenes").mkdir(parents=True, exist_ok=True)
    commands, final_output = build_commands(project, output_dir, aspect_ratio=aspect_ratio)
    for command in commands:
        if cancel_event and cancel_event.is_set():
            raise RenderError("Đã hủy quá trình dựng video.")
        on_log(command.label)
        process = subprocess.Popen(
            command.argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=subprocess_environment(),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        assert process.stdout is not None
        for line in process.stdout:
            on_log(line.rstrip())
            if cancel_event and cancel_event.is_set():
                process.terminate()
                process.wait(timeout=10)
                raise RenderError("Đã hủy quá trình dựng video.")
        code = process.wait()
        if code != 0:
            raise RenderError(f"Bước '{command.label}' thất bại với mã lỗi {code}.")
    if not final_output.is_file():
        raise RenderError("Renderer kết thúc nhưng không tạo được final.mp4.")
    return final_output
