import json
import tempfile
import unittest
from pathlib import Path

from whiteboard_app.voice import VoiceSettings, build_omnivoice_command


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
        self.assertEqual(command[-2], "--output")

    def test_settings_round_trip_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "settings.json"
            VoiceSettings(cli_path=r"E:\\Dự án AI\\omnivoice-infer.exe").save(target)
            loaded = VoiceSettings.load(target)
            self.assertEqual(loaded.cli_path, r"E:\\Dự án AI\\omnivoice-infer.exe")
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("omnivoiceCli", data)


if __name__ == "__main__":
    unittest.main()
