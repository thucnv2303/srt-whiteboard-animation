import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from whiteboard_app.project import load_project
from whiteboard_app.timeline import compile_timeline, wav_duration_ms


def write_silent_wav(path: Path, duration_ms: int) -> None:
    rate = 24000
    frames = round(rate * duration_ms / 1000)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\0\0" * frames)


class TimelineTests(unittest.TestCase):
    def test_compiles_audio_clock_into_runtime_annotation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scene.png").write_bytes(b"png")
            annotation = root / "scene.annotation.json"
            annotation.write_text(
                json.dumps(
                    {
                        "sceneDurationMs": 50000,
                        "elements": [
                            {"id": "food-1", "reveal": {"startMs": 500, "durationMs": 8000}},
                            {"id": "food-2", "reveal": {"startMs": 9500, "durationMs": 8000}},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "project.json").write_text(
                json.dumps(
                    {
                        "title": "Timeline",
                        "scenes": [
                            {
                                "id": "scene-01",
                                "image": "scene.png",
                                "annotation": "scene.annotation.json",
                            }
                        ],
                        "narration": [
                            {
                                "id": "cue-1",
                                "sceneId": "scene-01",
                                "text": "Món một",
                                "elementIds": ["food-1"],
                            },
                            {
                                "id": "cue-2",
                                "sceneId": "scene-01",
                                "text": "Món hai",
                                "elementIds": ["food-2"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            project = load_project(root)
            cue_1, cue_2 = root / "cue-1.wav", root / "cue-2.wav"
            write_silent_wav(cue_1, 4000)
            write_silent_wav(cue_2, 5000)

            def fake_run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"timeline-wave")
                return Mock(returncode=0, stderr="")

            with (
                patch("whiteboard_app.timeline.shutil.which", return_value="ffmpeg-fixture"),
                patch("whiteboard_app.timeline.subprocess.run", side_effect=fake_run),
            ):
                result = compile_timeline(
                    project,
                    {"cue-1": cue_1, "cue-2": cue_2},
                    root / "output",
                    lambda _line: None,
                )
            runtime = json.loads(
                result.runtime_annotations["scene-01"].read_text(encoding="utf-8")
            )
            self.assertEqual(result.total_duration_ms, 10400)
            self.assertEqual(runtime["sceneDurationMs"], 10400)
            self.assertEqual(runtime["elements"][0]["reveal"]["startMs"], 300)
            self.assertEqual(runtime["elements"][1]["reveal"]["startMs"], 4750)
            self.assertEqual(len(result.cues), 2)

    def test_reads_exact_wav_duration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "voice.wav"
            write_silent_wav(path, 3250)
            self.assertEqual(wav_duration_ms(path), 3250)


if __name__ == "__main__":
    unittest.main()
