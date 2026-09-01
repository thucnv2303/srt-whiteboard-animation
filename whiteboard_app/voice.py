from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class OmniVoiceError(RuntimeError):
    """Lỗi OmniVoice có nội dung phù hợp để hiển thị trên UI."""


def settings_path() -> Path:
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / "NetChuyenDong" / "settings.json"


@dataclass(frozen=True)
class VoiceSettings:
    cli_path: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceSettings":
        target = path or settings_path()
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
            return cls(cli_path=shutil.which("omnivoice-infer") or "")
        value = data.get("omnivoiceCli", "") if isinstance(data, dict) else ""
        return cls(cli_path=value if isinstance(value, str) else "")

    def save(self, path: Path | None = None) -> None:
        target = path or settings_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps({"omnivoiceCli": self.cli_path}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


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
