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
    generate_scene_voices,
    prepare_synthesis_text,
    protect_voice_onset,
)


class OmniVoiceTests(unittest.TestCase):
    def test_synthesis_text_has_non_spoken_leading_context(self) -> None:
        self.assertEqual(prepare_synthesis_text("Hai, bò xào."), "Hai, bò xào.")

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
            boost = protect_voice_onset(path, leading_silence_ms=30)
            with wave.open(str(path), "rb") as audio:
                result = array("h")
                result.frombytes(audio.readframes(audio.getnframes()))
                self.assertEqual(audio.getframerate(), rate)
                self.assertEqual(audio.getnframes(), round(rate * 0.83))
            self.assertEqual(boost, 0.0)

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
                    VoiceProfile(
                        "voice-1", "Mẹ Dâu", sample, sample, 6.2, 91, 25.4,
                        reference_text="Câu nói mẫu đối chiếu cho voice clone.",
                    )
                ],
                path=target,
            )
            library.save()
            loaded = VoiceLibrary.load(target)
            self.assertEqual(len(loaded.profiles), 1)
            self.assertEqual(loaded.profiles[0].name, "Mẹ Dâu")
            self.assertEqual(loaded.profiles[0].quality_score, 91)
            self.assertEqual(loaded.profiles[0].reference_text, "Câu nói mẫu đối chiếu cho voice clone.")

    def test_adaptive_onset_energy_compensation_boosts_weak_onset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weak_cue.wav"
            rate = 24000
            # Đầu yếu (hụt hơi): 500 trong 0.25s, thân mạnh 6000 trong 1.0s
            weak_onset = array("h", [500] * round(rate * 0.25))
            strong_body = array("h", [6000] * round(rate * 1.0))
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(rate)
                audio.writeframes((weak_onset + strong_body).tobytes())

            boost = protect_voice_onset(path, leading_silence_ms=30)
            self.assertGreater(boost, 0.0)

            with wave.open(str(path), "rb") as audio:
                result = array("h")
                result.frombytes(audio.readframes(audio.getnframes()))
                # Mẫu đầu tiên sau silence pad phải lớn hơn mức 500 ban đầu
                silence_samples = round(rate * 30 / 1000)
                first_speech_sample = result[silence_samples]
                self.assertGreater(first_speech_sample, 500)

    def test_delete_profile_removes_from_library_and_deletes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "voices.json"
            sample = Path(directory) / "voice.wav"
            sample.write_bytes(b"wav content")
            profile = VoiceProfile("v-del", "Voice to delete", sample, sample, 4.0, 90, 20.0)
            library = VoiceLibrary(profiles=[profile], path=target)
            library.save()

            self.assertTrue(sample.is_file())
            success = library.delete_profile("v-del")
            self.assertTrue(success)
            self.assertEqual(len(library.profiles), 0)
            self.assertFalse(sample.is_file())

            # Verify reload
            reloaded = VoiceLibrary.load(target)
            self.assertEqual(len(reloaded.profiles), 0)

    def test_generate_scene_voices_creates_manifest_per_scene(self) -> None:
        from unittest.mock import Mock, patch
        from whiteboard_app.project import NarrationCue, Scene, VideoProject

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref_audio = root / "ref.wav"
            ref_audio.write_bytes(b"wav")
            out_dir = root / "out"

            project = VideoProject(
                root=root,
                manifest_path=root / "project.json",
                title="Test Scene Voice",
                version=1,
                scenes=[
                    Scene("s1", "Scene 1", root / "s1.png", root / "s1.json"),
                    Scene("s2", "Scene 2", root / "s2.png", root / "s2.json"),
                ],
                narration_cues=[
                    NarrationCue("c1", "s1", "Câu 1 của cảnh 1.", ["e1"]),
                    NarrationCue("c2", "s1", "Câu 2 của cảnh 1.", ["e2"]),
                    NarrationCue("c3", "s2", "Câu 1 của cảnh 2.", ["e3"]),
                ],
            )

            # Fake cli python environment
            fake_scripts = root / "Scripts"
            fake_scripts.mkdir(parents=True)
            fake_cli = fake_scripts / "omnivoice-infer.exe"
            fake_cli.write_bytes(b"")
            fake_py = root / "python.exe"
            fake_py.write_bytes(b"")

            def fake_popen(cmd, **kwargs):
                manifest_path = Path(cmd[cmd.index("--manifest") + 1])
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                for c in data["cues"]:
                    out_p = Path(c["output"])
                    out_p.parent.mkdir(parents=True, exist_ok=True)
                    # Write minimal valid wav
                    with wave.open(str(out_p), "wb") as w:
                        w.setnchannels(1)
                        w.setsampwidth(2)
                        w.setframerate(24000)
                        w.writeframes(b"\x00\x10" * 2400)
                mock_proc = Mock()
                mock_proc.stdout = ["Generating...", "Done."]
                mock_proc.wait.return_value = 0
                return mock_proc

            with patch("whiteboard_app.voice.subprocess.Popen", side_effect=fake_popen):
                result = generate_scene_voices(
                    cli_path=str(fake_cli),
                    project=project,
                    reference_audio=ref_audio,
                    output_dir=out_dir,
                    on_log=lambda _: None,
                )

            self.assertIn("s1", result)
            self.assertIn("s2", result)
            self.assertTrue(result["s1"].is_file())
            self.assertTrue(result["s2"].is_file())

            manifest_data = json.loads((out_dir / "scene-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest_data["cues"]), 2)
            self.assertEqual(manifest_data["cues"][0]["id"], "s1")
            self.assertEqual(manifest_data["cues"][0]["text"], "Câu 1 của cảnh 1. Câu 2 của cảnh 1.")
            self.assertEqual(manifest_data["cues"][1]["id"], "s2")
            self.assertEqual(manifest_data["cues"][1]["text"], "Câu 1 của cảnh 2.")


if __name__ == "__main__":
    unittest.main()
