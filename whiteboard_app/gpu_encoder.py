"""Phát hiện và chọn encoder phần cứng GPU tốt nhất trên máy hiện tại.

Thứ tự ưu tiên:
  1. h264_nvenc  — NVIDIA NVENC (nhanh nhất, chất lượng cao)
  2. h264_mf     — Windows MediaFoundation (dùng chip GPU qua OS layer)
  3. libx264     — CPU fallback (luôn hoạt động)

Kết quả được cache lại lần đầu tiên probe, không probe lại.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class EncoderInfo:
    """Thông tin encoder đã phát hiện."""
    name: str                    # Tên encoder FFmpeg (vd: "h264_nvenc")
    label: str                   # Tên hiển thị trên UI
    is_hardware: bool            # True nếu dùng GPU
    ffmpeg_args: list[str]       # Các tham số FFmpeg cho encoder này


# Danh sách encoder theo thứ tự ưu tiên
_ENCODER_CANDIDATES: list[tuple[str, str, bool, list[str]]] = [
    (
        "h264_nvenc",
        "NVIDIA NVENC (GPU)",
        True,
        ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-pix_fmt", "yuv420p"],
    ),
    (
        "h264_mf",
        "Windows MediaFoundation (GPU)",
        True,
        ["-c:v", "h264_mf", "-b:v", "15M", "-pix_fmt", "yuv420p"],
    ),
    (
        "libx264",
        "libx264 (CPU)",
        False,
        ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p"],
    ),
]

# Module-level cache
_cached: EncoderInfo | None = None
_probed: bool = False


def _probe_encoder(ffmpeg: str, encoder_name: str) -> bool:
    """Kiểm tra encoder có hoạt động trên máy không bằng cách encode 1 frame test."""
    try:
        result = subprocess.run(
            [
                ffmpeg, "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.04:r=25",
                "-frames:v", "1",
                "-c:v", encoder_name,
                "-f", "null", "-",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def detect_best_encoder(force_reprobe: bool = False) -> EncoderInfo:
    """Probe hệ thống và trả về encoder tốt nhất.

    Kết quả được cache nên các lần gọi sau trả về tức thì.
    """
    global _cached, _probed
    if _probed and not force_reprobe and _cached is not None:
        return _cached

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        _cached = EncoderInfo(
            name="libx264",
            label="libx264 (CPU — chưa cài FFmpeg)",
            is_hardware=False,
            ffmpeg_args=["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p"],
        )
        _probed = True
        return _cached

    for name, label, is_hw, args in _ENCODER_CANDIDATES:
        if _probe_encoder(ffmpeg, name):
            _cached = EncoderInfo(name=name, label=label, is_hardware=is_hw, ffmpeg_args=args)
            _probed = True
            return _cached

    # Không nên xảy ra — libx264 luôn có trong FFmpeg
    _cached = EncoderInfo(
        name="libx264",
        label="libx264 (CPU)",
        is_hardware=False,
        ffmpeg_args=["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p"],
    )
    _probed = True
    return _cached


def encoder_ffmpeg_args() -> list[str]:
    """Trả về danh sách tham số FFmpeg cho encoder tốt nhất (tiện dùng nhanh)."""
    return list(detect_best_encoder().ffmpeg_args)


def encoder_label() -> str:
    """Tên encoder đang dùng để hiển thị trên log/UI."""
    return detect_best_encoder().label
