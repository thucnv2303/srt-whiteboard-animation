import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from whiteboard_app.project import load_project
from whiteboard_app.renderer import (
    build_commands,
    create_video_poster,
    create_video_preview_audio,
    subprocess_environment,
)


class RendererCommandTests(unittest.TestCase):
    def test_child_process_is_forced_to_utf8(self) -> None:
        with patch.dict(os.environ, {"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}):
            environment = subprocess_environment()
        self.assertEqual(environment["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(environment["PYTHONUTF8"], "1")

    def test_builds_scene_and_merge_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_dir = root / "project"
            repo = root / "repo"
            project_dir.mkdir()
            for required in (
                repo / "scripts" / "render_stream_whiteboard.py",
                repo / "scripts" / "merge_scenes.py",
                repo / "assets" / "drawing-hand.png",
            ):
                required.parent.mkdir(parents=True, exist_ok=True)
                required.write_bytes(b"fixture")
            (project_dir / "scene.png").write_bytes(b"png")
            (project_dir / "scene.annotation.json").write_text("{}", encoding="utf-8")
            (project_dir / "project.json").write_text(
                json.dumps(
                    {
                        "title": "Demo",
                        "scenes": [
                            {
                                "id": "scene-01",
                                "image": "scene.png",
                                "annotation": "scene.annotation.json",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            project = load_project(project_dir)
            project.pen_brand = "Ăn dặm mẹ Dâu"
            with patch("whiteboard_app.renderer.repository_root", return_value=repo):
                commands, final = build_commands(project, root / "output", "python-fixture")
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[0].argv[0], "python-fixture")
            self.assertEqual(commands[0].label, "Dựng cảnh 1/1 — scene-01")
            self.assertIn("--pen-brand", commands[0].argv)
            self.assertIn("Ăn dặm mẹ Dâu", commands[0].argv)
            self.assertIn("--inputs", commands[1].argv)
            self.assertEqual(final, (root / "output" / "final.mp4").resolve())

            runtime_annotation = root / "runtime.annotation.json"
            runtime_annotation.write_text("{}", encoding="utf-8")
            project.runtime_annotations["scene-01"] = runtime_annotation
            with patch("whiteboard_app.renderer.repository_root", return_value=repo):
                runtime_commands, _ = build_commands(project, root / "runtime-output", "python-fixture")
            self.assertIn(str(runtime_annotation), runtime_commands[0].argv)

            voice = project_dir / "voice.wav"
            voice.write_bytes(b"voice")
            project.voice = voice
            with (
                patch("whiteboard_app.renderer.repository_root", return_value=repo),
                patch("whiteboard_app.renderer.shutil.which", return_value="ffmpeg-fixture"),
            ):
                commands_with_voice, _ = build_commands(project, root / "output", "python-fixture")
            self.assertEqual(commands_with_voice[-1].label, "Gắn voice vào video")
            self.assertIn("apad", commands_with_voice[-1].argv)

    def test_vertical_output_adds_ffmpeg_crop_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_dir = root / "project"
            repo = root / "repo"
            project_dir.mkdir()
            for required in (
                repo / "scripts" / "render_stream_whiteboard.py",
                repo / "scripts" / "merge_scenes.py",
                repo / "assets" / "drawing-hand.png",
            ):
                required.parent.mkdir(parents=True, exist_ok=True)
                required.write_bytes(b"fixture")
            (project_dir / "scene.png").write_bytes(b"png")
            (project_dir / "scene.annotation.json").write_text("{}", encoding="utf-8")
            (project_dir / "project.json").write_text(
                json.dumps(
                    {
                        "title": "Demo dọc",
                        "scenes": [
                            {
                                "id": "scene-01",
                                "image": "scene.png",
                                "annotation": "scene.annotation.json",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            project = load_project(project_dir)
            with (
                patch("whiteboard_app.renderer.repository_root", return_value=repo),
                patch("whiteboard_app.renderer.shutil.which", return_value="ffmpeg-fixture"),
            ):
                commands, final = build_commands(
                    project, root / "output", "python-fixture", aspect_ratio="9:16"
                )
            self.assertEqual(len(commands), 3)
            self.assertEqual(commands[-1].label, "Định dạng video 9:16 — 1080×1920")
            self.assertIn(
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                commands[-1].argv,
            )
            self.assertEqual(final, (root / "output" / "final.mp4").resolve())

    def test_creates_poster_for_result_preview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "final.mp4"
            poster = root / "preview.jpg"
            video.write_bytes(b"video")

            def fake_run(command: list[str], **_kwargs: object) -> Mock:
                Path(command[-1]).write_bytes(b"poster")
                return Mock(returncode=0)

            with (
                patch("whiteboard_app.renderer.shutil.which", return_value="ffmpeg-fixture"),
                patch("whiteboard_app.renderer.subprocess.run", side_effect=fake_run) as run,
            ):
                result = create_video_poster(video, poster)
            self.assertEqual(result, poster)
            self.assertIn("-frames:v", run.call_args.args[0])

    def test_extracts_pcm_audio_for_embedded_player(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "final.mp4"
            audio = root / "preview-audio.wav"
            video.write_bytes(b"video")

            def fake_run(command: list[str], **_kwargs: object) -> Mock:
                Path(command[-1]).write_bytes(b"wav")
                return Mock(returncode=0)

            with (
                patch("whiteboard_app.renderer.shutil.which", return_value="ffmpeg-fixture"),
                patch("whiteboard_app.renderer.subprocess.run", side_effect=fake_run) as run,
            ):
                result = create_video_preview_audio(video, audio)
            self.assertEqual(result, audio)
            self.assertIn("pcm_s16le", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
