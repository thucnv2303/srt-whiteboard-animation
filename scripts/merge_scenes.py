#!/usr/bin/env python3
"""
多幕合并：把各场景的白板动画 MP4 按顺序硬切拼接成一条完整视频。

优先用系统 ffmpeg 无损拼接（-c copy，不重编码）；各片尺寸/编码不一致或无
ffmpeg 时，回退到 PyAV 逐帧重编码并缩放补边到第一段尺寸。单片仍保留。

用法：
  <ENV_PY> merge_scenes.py --inputs a.mp4 b.mp4 c.mp4 --output final.mp4
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _get_video_duration(path: Path) -> float:
    try:
        import av
        with av.open(str(path)) as container:
            if container.streams.video:
                s = container.streams.video[0]
                if s.duration and s.time_base:
                    return float(s.duration * s.time_base)
            if container.duration:
                return float(container.duration / 1_000_000)
    except Exception:
        pass
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        res = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            try:
                return float(res.stdout.strip())
            except ValueError:
                pass
    return 0.0


def _ffmpeg_xfade(
    inputs: list[Path],
    output: Path,
    transition: str = "slideleft",
    duration: float = 0.35,
) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None or len(inputs) < 2 or transition in ("none", "copy"):
        return False

    durations = [_get_video_duration(p) for p in inputs]
    if any(d <= duration + 0.1 for d in durations):
        print("  [warn] Một số cảnh quá ngắn để áp dụng xfade, chuyển sang concat.")
        return False

    filter_chains = []
    prev_label = "0:v"
    cur_offset = 0.0
    for i in range(1, len(inputs)):
        cur_offset += durations[i - 1] - duration
        next_label = f"v{i}"
        filter_chains.append(
            f"[{prev_label}][{i}:v]xfade=transition={transition}:duration={duration:.3f}:offset={cur_offset:.3f}[{next_label}]"
        )
        prev_label = next_label

    filter_str = ";".join(filter_chains)
    inputs_args = []
    for p in inputs:
        inputs_args.extend(["-i", str(p)])

    encoder_configs = [
        ("h264_nvenc", ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-pix_fmt", "yuv420p"]),
        ("h264_mf",    ["-c:v", "h264_mf", "-b:v", "15M", "-pix_fmt", "yuv420p"]),
        ("libx264",    ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p"]),
    ]

    for enc_name, enc_args in encoder_configs:
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            *inputs_args,
            "-filter_complex", filter_str,
            "-map", f"[{prev_label}]",
            *enc_args,
            str(output),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and output.is_file():
            hw_tag = "GPU" if enc_name != "libx264" else "CPU"
            print(f"  ffmpeg xfade chuyển cảnh ({transition} {duration}s) hoàn tất ({enc_name} {hw_tag}): {output}")
            return True

    print("  [warn] ffmpeg xfade thất bại, chuyển sang concat.")
    return False


def _ffmpeg_concat_copy(inputs: list[Path], output: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in inputs:
            f.write(f"file '{p.resolve().as_posix()}'\n")
        list_path = Path(f.name)
    try:
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c", "copy", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 无损拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg -c copy 失败，尝试 GPU 重编码: {res.stderr.strip()[:200]}")
        # Thử GPU encoder trước khi fallback CPU
        encoder_configs = [
            ("h264_nvenc", ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18", "-pix_fmt", "yuv420p"]),
            ("h264_mf",    ["-c:v", "h264_mf", "-b:v", "15M", "-pix_fmt", "yuv420p"]),
            ("libx264",    ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p"]),
        ]
        for enc_name, enc_args in encoder_configs:
            res = subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", str(list_path), *enc_args,
                 "-vf", "scale='trunc(iw/2)*2':'trunc(ih/2)*2'", str(output)],
                capture_output=True, text=True,
            )
            if res.returncode == 0:
                hw_tag = "GPU" if enc_name != "libx264" else "CPU"
                print(f"  ffmpeg 重编码拼接完成({enc_name} {hw_tag}): {output}")
                return True
        print(f"  [warn] ffmpeg 重编码也失败")
        return False
    finally:
        list_path.unlink(missing_ok=True)


def _pyav_concat(inputs: list[Path], output: Path) -> bool:
    try:
        import av
    except ImportError:
        return False
    import numpy as np  # noqa: F401
    first = av.open(str(inputs[0]))
    vs = first.streams.video[0]
    w, h = vs.codec_context.width, vs.codec_context.height
    rate = vs.average_rate
    first.close()

    out = av.open(str(output), mode="w")
    ostream = out.add_stream("h264", rate=rate)
    ostream.width, ostream.height = w, h
    ostream.pix_fmt = "yuv420p"
    ostream.options = {"crf": "24", "preset": "medium"}
    for p in inputs:
        cont = av.open(str(p))
        for frame in cont.decode(video=0):
            if frame.width != w or frame.height != h:
                frame = frame.reformat(width=w, height=h)
            for pkt in ostream.encode(frame):
                out.mux(pkt)
        cont.close()
    for pkt in ostream.encode(None):
        out.mux(pkt)
    out.close()
    print(f"  PyAV 拼接完成: {output}")
    return True


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="按顺序合并多幕白板动画 MP4")
    p.add_argument("--inputs", nargs="+", required=True, help="按播放顺序的 MP4 列表")
    p.add_argument("--output", required=True, help="合并输出路径")
    p.add_argument("--transition", default="slideleft", help="Hiệu ứng chuyển cảnh (slideleft, wipeleft, fade, copy)")
    p.add_argument("--transition-duration", type=float, default=0.35, help="Thời lượng hiệu ứng chuyển cảnh (giây)")
    args = p.parse_args(argv)

    inputs = [Path(x) for x in args.inputs]
    missing = [str(x) for x in inputs if not x.exists()]
    if missing:
        print(f"[err] 缺少输入文件: {', '.join(missing)}", file=sys.stderr)
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if (
        (args.transition not in ("copy", "none") and _ffmpeg_xfade(inputs, output, transition=args.transition, duration=args.transition_duration))
        or _ffmpeg_concat_copy(inputs, output)
        or _pyav_concat(inputs, output)
    ):
        print(f"OUTPUT={output.resolve()}")
        return 0
    print("[err] 合并失败：系统无 ffmpeg 且 PyAV 不可用", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
