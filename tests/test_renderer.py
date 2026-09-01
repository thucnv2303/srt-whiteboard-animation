import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from whiteboard_app.project import load_project
from whiteboard_app.renderer import build_commands, subprocess_environment


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
            with patch("whiteboard_app.renderer.repository_root", return_value=repo):
                commands, final = build_commands(project, root / "output", "python-fixture")
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[0].argv[0], "python-fixture")
            self.assertEqual(commands[0].label, "Dựng cảnh 1/1 — scene-01")
            self.assertIn("--inputs", commands[1].argv)
            self.assertEqual(final, (root / "output" / "final.mp4").resolve())

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


if __name__ == "__main__":
    unittest.main()
