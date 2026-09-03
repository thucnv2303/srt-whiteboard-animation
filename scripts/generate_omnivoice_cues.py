#!/usr/bin/env python3
from __future__ import annotations

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
    parser.add_argument("--model", default="k2-fsa/OmniVoice")
    parser.add_argument("--language", default="vi")
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cues = data.get("cues", [])
    if not cues:
        raise ValueError("Manifest không có narration cue.")

    device = args.device or get_best_device()
    print(f"Đang nạp OmniVoice trên {device}…", flush=True)
    model = OmniVoice.from_pretrained(args.model, device_map=device, dtype=torch.float16)
    prompt = model.create_voice_clone_prompt(ref_audio=args.ref_audio)

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
