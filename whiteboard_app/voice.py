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
import sys
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .project import NarrationCue


class OmniVoiceError(RuntimeError):
    """Lỗi OmniVoice có nội dung phù hợp để hiển thị trên UI."""


def prepare_synthesis_text(text: str) -> str:
    """Cho model một nhịp đệm token trước từ đầu tiên mà không thêm lời đọc."""
    return f"… {text.strip()}"


def protect_voice_onset(path: Path, leading_silence_ms: int = 60) -> float:
    """Nâng thích ứng phụ âm đầu và thêm đệm an toàn; trả mức boost tối đa theo dB."""
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            rate = source.getframerate()
            frames = source.readframes(source.getnframes())
    except (OSError, wave.Error) as exc:
        raise OmniVoiceError(f"Không đọc được cue voice để bảo vệ âm đầu: {path}") from exc
    if channels != 1 or sample_width != 2 or rate <= 0:
        raise OmniVoiceError("Cue voice phải là WAV PCM 16-bit mono để cân bằng âm đầu.")
    samples = array("h")
    samples.frombytes(frames)
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        raise OmniVoiceError(f"Cue voice rỗng: {path}")

    block_samples = max(1, round(rate * 0.01))
    levels = [
        audioop.rms(samples[start:start + block_samples].tobytes(), 2)
        for start in range(0, len(samples), block_samples)
    ]
    peak_level = max(levels, default=0)
    threshold = max(180, round(peak_level * 0.04))
    onset_block = next((index for index, level in enumerate(levels) if level >= threshold), 0)
    first_levels = levels[onset_block:onset_block + 10]
    reference_levels = sorted(levels[onset_block + 10:onset_block + 70])
    first_rms = math.sqrt(sum(level * level for level in first_levels) / max(1, len(first_levels)))
    if reference_levels:
        reference = reference_levels[min(len(reference_levels) - 1, round(len(reference_levels) * 0.7))]
    else:
        reference = first_rms
    target = reference * 0.72
    gain = min(1.8, max(1.0, target / max(1.0, first_rms)))

    onset_sample = onset_block * block_samples
    hold_samples = max(1, round(rate * 0.06))
    release_samples = max(1, round(rate * 0.08))
    protected = array("h", samples)
    for index in range(onset_sample, min(len(protected), onset_sample + hold_samples + release_samples)):
        relative = index - onset_sample
        if relative < hold_samples:
            local_gain = gain
        else:
            progress = (relative - hold_samples) / release_samples
            local_gain = gain + (1.0 - gain) * progress
        value = protected[index] * local_gain
        absolute = abs(value)
        if absolute > 30000:
            value = math.copysign(30000 + (absolute - 30000) * 0.2, value)
        protected[index] = max(-32767, min(32767, round(value)))

    padding = array("h", [0]) * max(0, round(rate * leading_silence_ms / 1000))
    output_samples = padding + protected
    temporary = path.with_suffix(".onset.tmp.wav")
    try:
        with wave.open(str(temporary), "wb") as target_file:
            target_file.setnchannels(1)
            target_file.setsampwidth(2)
            target_file.setframerate(rate)
            if sys.byteorder != "little":
                output_samples.byteswap()
            target_file.writeframes(output_samples.tobytes())
        temporary.replace(path)
    except (OSError, wave.Error) as exc:
        temporary.unlink(missing_ok=True)
        raise OmniVoiceError(f"Không thể ghi cue voice đã cân bằng: {path}") from exc
    return 20 * math.log10(gain)


def settings_path() -> Path:
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / "NetChuyenDong" / "settings.json"


def voice_library_path() -> Path:
    return settings_path().parent / "voices.json"


def voice_assets_dir() -> Path:
    return settings_path().parent / "voices"


def load_settings_data(path: Path | None = None) -> dict[str, object]:
    target = path or settings_path()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings_data(data: dict[str, object], path: Path | None = None) -> None:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


@dataclass(frozen=True)
class VoiceSettings:
    cli_path: str = ""
    selected_profile_id: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceSettings":
        target = path or settings_path()
        data = load_settings_data(target)
        if not data:
            return cls(cli_path=shutil.which("omnivoice-infer") or "")
        value = data.get("omnivoiceCli", shutil.which("omnivoice-infer") or "")
        selected = data.get("selectedVoiceProfile", "") if isinstance(data, dict) else ""
        return cls(
            cli_path=value if isinstance(value, str) else "",
            selected_profile_id=selected if isinstance(selected, str) else "",
        )

    def save(self, path: Path | None = None) -> None:
        target = path or settings_path()
        data = load_settings_data(target)
        data.update(
            {
                "omnivoiceCli": self.cli_path,
                "selectedVoiceProfile": self.selected_profile_id,
            }
        )
        save_settings_data(data, target)


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


def python_for_omnivoice_cli(cli_path: str) -> Path:
    cli = Path(cli_path).expanduser().resolve()
    if os.name == "nt":
        python = cli.parent.parent / "python.exe"
    else:
        python = cli.parent / "python"
    if not python.is_file():
        raise OmniVoiceError(
            "Không tìm thấy Python của môi trường OmniVoice cạnh file CLI. "
            "Hãy chọn omnivoice-infer.exe trong thư mục Scripts của môi trường đã cài OmniVoice."
        )
    return python


def generate_cue_voices(
    cli_path: str,
    cues: list[NarrationCue],
    reference_audio: Path,
    output_dir: Path,
    on_log: Callable[[str], None],
    cancel_event: threading.Event | None = None,
) -> dict[str, Path]:
    if not cues:
        raise OmniVoiceError("Dự án chưa có narration cue để đồng bộ timeline.")
    if not reference_audio.is_file():
        raise OmniVoiceError(f"Không tìm thấy giọng mẫu: {reference_audio}")
    python = python_for_omnivoice_cli(cli_path)
    helper = Path(__file__).resolve().parents[1] / "scripts" / "generate_omnivoice_cues.py"
    if not helper.is_file():
        raise OmniVoiceError(f"Thiếu bộ tạo voice timeline: {helper}")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        cue.cue_id: output_dir / f"{index:02d}-{cue.cue_id}.wav"
        for index, cue in enumerate(cues, start=1)
    }
    manifest = output_dir / "cue-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "cues": [
                    {
                        "id": cue.cue_id,
                        "text": cue.text,
                        "synthesisText": prepare_synthesis_text(cue.text),
                        "output": str(outputs[cue.cue_id]),
                    }
                    for cue in cues
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    command = [
        str(python),
        str(helper),
        "--manifest",
        str(manifest),
        "--ref-audio",
        str(reference_audio.resolve()),
        "--language",
        "vi",
    ]
    on_log(f"Đang tạo {len(cues)} đoạn voice; OmniVoice chỉ nạp model một lần…")
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
            raise OmniVoiceError("Đã hủy tạo voice timeline.")
    code = process.wait()
    if code != 0:
        raise OmniVoiceError(f"Tạo voice timeline thất bại với mã lỗi {code}.")
    missing = [str(path) for path in outputs.values() if not path.is_file()]
    if missing:
        raise OmniVoiceError(f"OmniVoice chưa tạo đủ cue: {', '.join(missing)}")
    for cue in cues:
        boost_db = protect_voice_onset(outputs[cue.cue_id])
        on_log(f"Đã bảo vệ âm đầu {cue.cue_id}: +{boost_db:.1f} dB, đệm 60 ms.")
    return outputs
