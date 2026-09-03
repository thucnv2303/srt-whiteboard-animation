import json
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

from whiteboard_app.preferences import VideoPreferences
from whiteboard_app.voice import (
    VoiceLibrary,
    VoiceProfile,
    VoiceSettings,
    build_omnivoice_command,
    choose_best_segment,
    prepare_synthesis_text,
    protect_voice_onset,
)


class OmniVoiceTests(unittest.TestCase):
    def test_synthesis_text_has_non_spoken_leading_context(self) -> None:
        self.assertEqual(prepare_synthesis_text("Hai, bò xào."), "… Hai, bò xào.")

    def test_protects_quiet_first_phoneme_without_changing_sample_rate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cue.wav"
            rate = 24000
            quiet = array("h", [900] * round(rate * 0.1))
            body = array("h", [6000] * round(rate * 0.7))
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(rate)
                audio.writeframes((quiet + body).tobytes())
            boost = protect_voice_onset(path, leading_silence_ms=60)
            with wave.open(str(path), "rb") as audio:
                result = array("h")
                result.frombytes(audio.readframes(audio.getnframes()))
                self.assertEqual(audio.getframerate(), rate)
                self.assertEqual(audio.getnframes(), round(rate * 0.86))
            pad = round(rate * 0.06)
            self.assertGreater(boost, 3.0)
            self.assertGreater(max(result[pad:pad + round(rate * 0.06)]), 1400)

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

    def test_video_choices_and_voice_settings_preserve_each_other(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "settings.json"
            VideoPreferences(aspect_ratio="9:16", pen_brand="Mẹ Dâu").save(target)
            VoiceSettings(cli_path="omnivoice.exe", selected_profile_id="voice-1").save(target)

            video = VideoPreferences.load(target)
            voice = VoiceSettings.load(target)
            self.assertEqual(video.aspect_ratio, "9:16")
            self.assertEqual(video.pen_brand, "Mẹ Dâu")
            self.assertEqual(voice.cli_path, "omnivoice.exe")
            self.assertEqual(voice.selected_profile_id, "voice-1")
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
