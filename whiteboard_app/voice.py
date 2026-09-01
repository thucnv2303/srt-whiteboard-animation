from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
import uuid
import wave
import audioop
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class OmniVoiceError(RuntimeError):
    """Lỗi OmniVoice có nội dung phù hợp để hiển thị trên UI."""


def settings_path() -> Path:
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / "NetChuyenDong" / "settings.json"


def voice_library_path() -> Path:
    return settings_path().parent / "voices.json"


def voice_assets_dir() -> Path:
    return settings_path().parent / "voices"


@dataclass(frozen=True)
class VoiceSettings:
    cli_path: str = ""
    selected_profile_id: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceSettings":
        target = path or settings_path()
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
            return cls(cli_path=shutil.which("omnivoice-infer") or "")
        value = data.get("omnivoiceCli", "") if isinstance(data, dict) else ""
        selected = data.get("selectedVoiceProfile", "") if isinstance(data, dict) else ""
        return cls(
            cli_path=value if isinstance(value, str) else "",
            selected_profile_id=selected if isinstance(selected, str) else "",
        )

    def save(self, path: Path | None = None) -> None:
        target = path or settings_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "omnivoiceCli": self.cli_path,
                    "selectedVoiceProfile": self.selected_profile_id,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True)
class VoiceProfile:
    profile_id: str
    name: str
    audio_path: Path
    source_path: Path
    duration_seconds: float
    quality_score: int
    snr_db: float

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "VoiceProfile":
        return cls(
            profile_id=str(data["id"]),
            name=str(data["name"]),
            audio_path=Path(str(data["audioPath"])),
            source_path=Path(str(data.get("sourcePath", data["audioPath"]))),
            duration_seconds=float(data.get("durationSeconds", 0)),
            quality_score=int(data.get("qualityScore", 0)),
            snr_db=float(data.get("snrDb", 0)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.profile_id,
            "name": self.name,
            "audioPath": str(self.audio_path),
            "sourcePath": str(self.source_path),
            "durationSeconds": round(self.duration_seconds, 3),
            "qualityScore": self.quality_score,
            "snrDb": round(self.snr_db, 2),
        }


@dataclass
class VoiceLibrary:
    profiles: list[VoiceProfile]
    path: Path

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceLibrary":
        target = path or voice_library_path()
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
            items = raw.get("profiles", []) if isinstance(raw, dict) else []
            profiles = [VoiceProfile.from_dict(item) for item in items if isinstance(item, dict)]
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError):
            profiles = []
        return cls(profiles=profiles, path=target)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"schemaVersion": 1, "profiles": [profile.to_dict() for profile in self.profiles]},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def get(self, profile_id: str) -> VoiceProfile | None:
        return next((profile for profile in self.profiles if profile.profile_id == profile_id), None)


@dataclass(frozen=True)
class AudioAnalysis:
    start_seconds: float
    duration_seconds: float
    noise_db: float
    signal_db: float
    snr_db: float
    quality_score: int


def choose_best_segment(
    levels: list[int],
    frame_seconds: float = 0.02,
    min_seconds: float = 3.0,
    max_seconds: float = 8.0,
) -> AudioAnalysis:
    if not levels or len(levels) * frame_seconds < min_seconds:
        raise OmniVoiceError("Mẫu giọng phải có ít nhất 3 giây âm thanh.")
    sorted_levels = sorted(levels)
    noise = max(1, sorted_levels[max(0, int(len(sorted_levels) * 0.2) - 1)])
    threshold = max(180, int(noise * 2.2))
    min_frames = max(1, int(min_seconds / frame_seconds))
    max_frames = max(min_frames, int(max_seconds / frame_seconds))
    gap_limit = max(1, int(0.35 / frame_seconds))

    spans: list[tuple[int, int]] = []
    start: int | None = None
    last_active = 0
    for index, level in enumerate(levels):
        if level >= threshold:
            if start is None:
                start = index
            last_active = index
        elif start is not None and index - last_active > gap_limit:
            spans.append((start, last_active + 1))
            start = None
    if start is not None:
        spans.append((start, last_active + 1))
    usable = [(start, end) for start, end in spans if end - start >= min_frames]
    if not usable:
        usable = [(0, len(levels))]

    best: tuple[float, int, int, float, float] | None = None
    step = max(1, int(0.25 / frame_seconds))
    for span_start, span_end in usable:
        window_frames = min(max_frames, span_end - span_start)
        if window_frames < min_frames:
            continue
        final_start = max(span_start, span_end - window_frames)
        for window_start in range(span_start, final_start + 1, step):
            window_end = min(span_end, window_start + window_frames)
            window = levels[window_start:window_end]
            signal = sum(window) / len(window)
            active_ratio = sum(level >= threshold for level in window) / len(window)
            snr = 20 * math.log10(max(signal, 1) / noise)
            score = snr + active_ratio * 12
            if best is None or score > best[0]:
                best = (score, window_start, window_end, signal, active_ratio)
    if best is None:
        raise OmniVoiceError("Không tìm thấy đoạn nói liên tục đủ 3 giây trong file mẫu.")

    _, start_frame, end_frame, signal, active_ratio = best
    snr = 20 * math.log10(max(signal, 1) / noise)
    quality = round(max(0, min(100, (snr - 4) * 4.2 + active_ratio * 35)))
    return AudioAnalysis(
        start_seconds=start_frame * frame_seconds,
        duration_seconds=(end_frame - start_frame) * frame_seconds,
        noise_db=20 * math.log10(noise / 32768),
        signal_db=20 * math.log10(max(signal, 1) / 32768),
        snr_db=snr,
        quality_score=quality,
    )


def analyze_pcm_wav(path: Path) -> AudioAnalysis:
    with wave.open(str(path), "rb") as audio:
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2:
            raise OmniVoiceError("File phân tích phải là WAV mono PCM 16-bit.")
        rate = audio.getframerate()
        frame_count = max(1, int(rate * 0.02))
        levels: list[int] = []
        while True:
            chunk = audio.readframes(frame_count)
            if not chunk:
                break
            levels.append(audioop.rms(chunk, 2))
    return choose_best_segment(levels)


def prepare_voice_profile(
    name: str,
    source_audio: Path,
    on_log: Callable[[str], None],
    library: VoiceLibrary | None = None,
    assets_dir: Path | None = None,
) -> VoiceProfile:
    if not name.strip():
        raise OmniVoiceError("Hãy đặt tên cho giọng đọc.")
    if not source_audio.is_file():
        raise OmniVoiceError(f"Không tìm thấy file âm thanh: {source_audio}")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise OmniVoiceError("Cần FFmpeg trong PATH để phân tích và làm sạch giọng mẫu.")

    target_library = library or VoiceLibrary.load()
    target_dir = assets_dir or voice_assets_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    profile_id = uuid.uuid4().hex
    output = target_dir / f"{profile_id}.wav"

    with tempfile.TemporaryDirectory(prefix="voice-analysis-") as directory:
        probe = Path(directory) / "source.wav"
        on_log("Đang chuẩn hóa mẫu về WAV mono 24 kHz…")
        probe_command = [
            ffmpeg, "-y", "-loglevel", "error", "-i", str(source_audio), "-vn",
            "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(probe),
        ]
        result = subprocess.run(probe_command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise OmniVoiceError(f"Không thể đọc file mẫu: {result.stderr.strip()}")
        analysis = analyze_pcm_wav(probe)
        on_log(
            f"Đã chọn đoạn {analysis.start_seconds:.2f}s–"
            f"{analysis.start_seconds + analysis.duration_seconds:.2f}s; "
            f"SNR ước tính {analysis.snr_db:.1f} dB."
        )
        filters = (
            "highpass=f=80,lowpass=f=8000,"
            "afftdn=nr=12:nf=-35,"
            "dynaudnorm=f=150:g=7,alimiter=limit=0.95"
        )
        clean_command = [
            ffmpeg, "-y", "-loglevel", "error", "-ss", f"{analysis.start_seconds:.3f}",
            "-t", f"{analysis.duration_seconds:.3f}", "-i", str(probe),
            "-af", filters, "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(output),
        ]
        result = subprocess.run(clean_command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0 or not output.is_file():
            raise OmniVoiceError(f"Làm sạch giọng mẫu thất bại: {result.stderr.strip()}")

    profile = VoiceProfile(
        profile_id=profile_id,
        name=name.strip(),
        audio_path=output.resolve(),
        source_path=source_audio.resolve(),
        duration_seconds=analysis.duration_seconds,
        quality_score=analysis.quality_score,
        snr_db=analysis.snr_db,
    )
    target_library.profiles.append(profile)
    target_library.save()
    on_log(f"Đã lưu giọng '{profile.name}' — chất lượng {profile.quality_score}/100.")
    return profile


def play_audio(path: Path) -> None:
    if not path.is_file():
        raise OmniVoiceError(f"Không tìm thấy file nghe thử: {path}")
    if os.name == "nt":
        import winsound

        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return
    player = shutil.which("ffplay")
    if player is None:
        raise OmniVoiceError("Không tìm thấy trình phát âm thanh.")
    subprocess.Popen([player, "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)])


def stop_audio() -> None:
    if os.name == "nt":
        import winsound

        winsound.PlaySound(None, winsound.SND_PURGE)


def build_omnivoice_command(
    cli_path: str,
    text: str,
    reference_audio: Path,
    output: Path,
    reference_text: str | None = None,
) -> list[str]:
    command = [
        cli_path,
        "--model",
        "k2-fsa/OmniVoice",
        "--text",
        text,
        "--language",
        "vi",
        "--ref_audio",
        str(reference_audio),
    ]
    if reference_text and reference_text.strip():
        command.extend(["--ref_text", reference_text.strip()])
    command.extend(["--output", str(output)])
    return command


def generate_clone_voice(
    cli_path: str,
    text: str,
    reference_audio: Path,
    output: Path,
    on_log: Callable[[str], None],
    cancel_event: threading.Event | None = None,
) -> Path:
    executable = Path(cli_path).expanduser()
    if not executable.is_file():
        raise OmniVoiceError(
            "Không tìm thấy OmniVoice CLI. Hãy chọn file omnivoice-infer.exe của bản đã cài trên máy."
        )
    if not reference_audio.is_file():
        raise OmniVoiceError(f"Không tìm thấy giọng mẫu: {reference_audio}")
    if not text.strip():
        raise OmniVoiceError("Lời thoại không được để trống.")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = build_omnivoice_command(str(executable), text.strip(), reference_audio.resolve(), output)
    on_log("Đang chạy OmniVoice dùng chung…")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert process.stdout is not None
    for line in process.stdout:
        on_log(line.rstrip())
        if cancel_event and cancel_event.is_set():
            process.terminate()
            process.wait(timeout=10)
            raise OmniVoiceError("Đã hủy tạo voice clone.")
    code = process.wait()
    if code != 0:
        raise OmniVoiceError(f"OmniVoice kết thúc với mã lỗi {code}.")
    if not output.is_file():
        raise OmniVoiceError("OmniVoice kết thúc nhưng không tạo được file voice.")
    return output
