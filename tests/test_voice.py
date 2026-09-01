import json
import tempfile
import unittest
from pathlib import Path

from whiteboard_app.voice import (
    VoiceLibrary,
    VoiceProfile,
    VoiceSettings,
    build_omnivoice_command,
    choose_best_segment,
)


class OmniVoiceTests(unittest.TestCase):
    def test_build_command_uses_external_cli_and_reference(self) -> None:
        command = build_omnivoice_command(
            r"E:\\OmniVoice\\omnivoice-infer.exe",
            "Xin chào bé",
            Path(r"E:\\voices\\mau.wav"),
            Path(r"E:\\output\\voice.wav"),
        )
        self.assertEqual(command[0], r"E:\\OmniVoice\\omnivoice-infer.exe")
        self.assertIn("--ref_audio", command)
        self.assertIn("Xin chào bé", command)
        self.assertIn("vi", command)
        self.assertEqual(command[-2], "--output")

    def test_settings_round_trip_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "settings.json"
            VoiceSettings(cli_path=r"E:\\Dự án AI\\omnivoice-infer.exe").save(target)
            loaded = VoiceSettings.load(target)
            self.assertEqual(loaded.cli_path, r"E:\\Dự án AI\\omnivoice-infer.exe")
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("omnivoiceCli", data)

    def test_selects_clean_continuous_voice_segment(self) -> None:
        levels = [80] * 100 + [4000] * 250 + [90] * 100
        analysis = choose_best_segment(levels, frame_seconds=0.02, min_seconds=3, max_seconds=8)
        self.assertGreaterEqual(analysis.start_seconds, 1.5)
        self.assertGreaterEqual(analysis.duration_seconds, 3)
        self.assertGreater(analysis.snr_db, 20)
        self.assertGreater(analysis.quality_score, 70)

    def test_voice_library_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "voices.json"
            sample = Path(directory) / "voice.wav"
            sample.write_bytes(b"wav")
            library = VoiceLibrary(
                profiles=[
                    VoiceProfile("voice-1", "Mẹ Dâu", sample, sample, 6.2, 91, 25.4)
                ],
                path=target,
            )
            library.save()
            loaded = VoiceLibrary.load(target)
            self.assertEqual(len(loaded.profiles), 1)
            self.assertEqual(loaded.profiles[0].name, "Mẹ Dâu")
            self.assertEqual(loaded.profiles[0].quality_score, 91)


if __name__ == "__main__":
    unittest.main()
