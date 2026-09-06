import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from whiteboard_app.project import load_project
from whiteboard_app.timeline import (
    compile_scene_timeline,
    compile_timeline,
    detect_cue_offsets_in_scene,
    wav_duration_ms,
)


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

    def test_compile_scene_timeline_allocates_adaptive_timing_and_gaze(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scene_01.png").write_bytes(b"png1")
            (root / "scene_02.png").write_bytes(b"png2")
            (root / "scene_01.annotation.json").write_text(
                json.dumps({
                    "elements": [
                        {"id": "el-1", "reveal": {"startMs": 0, "durationMs": 1000}},
                        {"id": "el-2", "reveal": {"startMs": 0, "durationMs": 1000}},
                    ]
                }),
                encoding="utf-8",
            )
            (root / "scene_02.annotation.json").write_text(
                json.dumps({
                    "elements": [
                        {"id": "el-3", "reveal": {"startMs": 0, "durationMs": 1000}},
                    ]
                }),
                encoding="utf-8",
            )
            (root / "project.json").write_text(
                json.dumps({
                    "title": "Scene Timeline",
                    "scenes": [
                        {"id": "s1", "image": "scene_01.png", "annotation": "scene_01.annotation.json"},
                        {"id": "s2", "image": "scene_02.png", "annotation": "scene_02.annotation.json"},
                    ],
                    "narration": [
                        {"id": "cue-1", "sceneId": "s1", "text": "Câu một cảnh một", "elementIds": ["el-1"]},
                        {"id": "cue-2", "sceneId": "s1", "text": "Câu hai cảnh một", "elementIds": ["el-2"]},
                        {"id": "cue-3", "sceneId": "s2", "text": "Câu một cảnh hai", "elementIds": ["el-3"]},
                    ],
                }),
                encoding="utf-8",
            )
            project = load_project(root)
            audio_s1 = root / "s1.wav"
            audio_s2 = root / "s2.wav"
            write_silent_wav(audio_s1, 5000)
            write_silent_wav(audio_s2, 4000)

            def fake_run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"scene-timeline-wav")
                return Mock(returncode=0, stderr="")

            with (
                patch("whiteboard_app.timeline.shutil.which", return_value="ffmpeg-fixture"),
                patch("whiteboard_app.timeline.subprocess.run", side_effect=fake_run),
            ):
                result = compile_scene_timeline(
                    project,
                    {"s1": audio_s1, "s2": audio_s2},
                    root / "output",
                    lambda _line: None,
                    gaze_ms=650,
                )

            self.assertEqual(result.total_duration_ms, 5000 + 650 + 4000 + 650)
            s1_ann = json.loads(result.runtime_annotations["s1"].read_text(encoding="utf-8"))
            s2_ann = json.loads(result.runtime_annotations["s2"].read_text(encoding="utf-8"))
            self.assertEqual(s1_ann["sceneDurationMs"], 5650)
            self.assertEqual(s2_ann["sceneDurationMs"], 4650)
            self.assertGreater(s1_ann["elements"][1]["reveal"]["startMs"], s1_ann["elements"][0]["reveal"]["startMs"])
            self.assertEqual(len(result.cues), 3)

    def test_detect_cue_offsets_in_scene_fallback_proportional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.wav"
            write_silent_wav(path, 10000)
            from whiteboard_app.project import NarrationCue
            cues = [
                NarrationCue("c1", "s1", "Đoạn một ngắn", ["e1"]),
                NarrationCue("c2", "s1", "Đoạn hai có độ dài dài hơn đoạn một", ["e2"]),
            ]
            offsets = detect_cue_offsets_in_scene(path, cues, scene_voice_dur_ms=10000, gaze_ms=650)
            self.assertEqual(len(offsets), 2)
            self.assertEqual(offsets[0], 0)
            self.assertGreater(offsets[1], 1000)
            self.assertLess(offsets[1], 10000)


if __name__ == "__main__":
    unittest.main()
