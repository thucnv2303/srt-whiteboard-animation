#!/usr/bin/env python3
from __future__ import annotations

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import argparse
import json
from pathlib import Path

import soundfile as sf
import torch
from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.common import get_best_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate many OmniVoice cues with one model load")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ref-audio", required=True)
    parser.add_argument("--ref-text", default=None)
    parser.add_argument("--model", default="k2-fsa/OmniVoice")
    parser.add_argument("--language", default="vi")
    parser.add_argument("--device", default=None)
    return parser.parse_args()


import os


def _resolve_reference_text(ref_audio: str, ref_text: str | None) -> str | None:
    if ref_text and ref_text.strip():
        return ref_text.strip()
    ref_path = Path(ref_audio).resolve()
    appdata = os.getenv("APPDATA")
    if appdata:
        voices_json = Path(appdata) / "NetChuyenDong" / "voices.json"
        if voices_json.is_file():
            try:
                data = json.loads(voices_json.read_text(encoding="utf-8"))
                for prof in data.get("profiles", []):
                    p_audio = Path(str(prof.get("audioPath", ""))).resolve()
                    if p_audio == ref_path:
                        text = prof.get("referenceText")
                        if text and text.strip():
                            print(f"  [SafeVoice] Tự động lấy ref_text từ voices.json: {text[:35]}…", flush=True)
                            return text.strip()
            except Exception:
                pass
    try:
        from faster_whisper import WhisperModel
        whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = whisper.transcribe(str(ref_path), language="vi")
        detected = " ".join(s.text for s in segments).strip()
        if detected:
            print(f"  [SafeVoice] Tự động trích xuất ref_text bằng Whisper: {detected[:35]}…", flush=True)
            return detected
    except Exception:
        pass
    return None


def main() -> None:
    args = parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cues = data.get("cues", [])
    if not cues:
        raise ValueError("Manifest không có narration cue.")

    device = args.device or get_best_device()
    print(f"Đang nạp OmniVoice trên {device}…", flush=True)
    model = OmniVoice.from_pretrained(args.model, device_map=device, dtype=torch.float16)
    ref_text = _resolve_reference_text(args.ref_audio, args.ref_text)
    prompt = model.create_voice_clone_prompt(ref_audio=args.ref_audio, ref_text=ref_text)

    for index, cue in enumerate(cues, start=1):
        output = Path(cue["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        print(f"VOICE_CUE {index}/{len(cues)} {cue['id']}", flush=True)
        audio = model.generate(
            text=cue.get("synthesisText", cue["text"]),
            language=args.language,
            voice_clone_prompt=prompt,
        )
        sf.write(output, audio[0], model.sampling_rate)
        print(f"VOICE_SAVED {cue['id']} {output}", flush=True)


if __name__ == "__main__":
    main()
