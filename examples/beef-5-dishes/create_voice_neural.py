from __future__ import annotations

import asyncio
from pathlib import Path

VOICE = "vi-VN-HoaiMyNeural"
RATE = "-5%"


async def create_voice() -> Path:
    try:
        import edge_tts
    except ImportError as exc:
        raise SystemExit(
            "Chưa có edge-tts. Hãy chạy create-voice-neural.bat để tự cài."
        ) from exc

    project_dir = Path(__file__).resolve().parent
    script = (project_dir / "script.txt").read_text(encoding="utf-8-sig").strip()
    output = project_dir / "voice.mp3"
    if not script:
        raise SystemExit("script.txt đang rỗng.")
    await edge_tts.Communicate(script, VOICE, rate=RATE).save(str(output))
    return output


if __name__ == "__main__":
    voice_path = asyncio.run(create_voice())
    print(f"Đã tạo voice Việt neural: {voice_path}")
