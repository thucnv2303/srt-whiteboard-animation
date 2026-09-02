import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from whiteboard_app.project import ProjectError, load_project


def make_project(root: Path, *, voice: bool = False) -> Path:
    (root / "scene.png").write_bytes(b"png")
    (root / "scene.annotation.json").write_text("{}", encoding="utf-8")
    data = {
        "schemaVersion": 1,
        "title": "Bữa ăn cho bé",
        "version": 1,
        "scenes": [
            {
                "id": "scene-01",
                "title": "Mở đầu",
                "image": "scene.png",
                "annotation": "scene.annotation.json",
            }
        ],
    }
    if voice:
        (root / "voice.mp3").write_bytes(b"mp3")
        data["voice"] = "voice.mp3"
    manifest = root / "project.json"
    manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return manifest


class ProjectTests(unittest.TestCase):
    def test_load_valid_folder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_project(root, voice=True)
            project = load_project(root)
            self.assertEqual(project.title, "Bữa ăn cho bé")
            self.assertEqual(len(project.scenes), 1)
            self.assertEqual(project.voice, root / "voice.mp3")

    def test_loads_gpt_script_and_scene_duration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            (root / "script.txt").write_text("Xin chào bé.", encoding="utf-8")
            (root / "scene.annotation.json").write_text(
                json.dumps({"sceneDurationMs": 8600}), encoding="utf-8"
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["script"] = "script.txt"
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            project = load_project(root)
            self.assertEqual(project.script_text, "Xin chào bé.")
            self.assertEqual(project.script_path, root / "script.txt")
            self.assertEqual(project.scenes[0].duration_ms, 8600)

    def test_rejects_declared_missing_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["script"] = "missing-script.txt"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ProjectError, "Không tìm thấy kịch bản"):
                load_project(root)

    def test_loads_narration_cue_mapped_to_element(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            (root / "scene.annotation.json").write_text(
                json.dumps(
                    {
                        "sceneDurationMs": 5000,
                        "elements": [{"id": "food-1", "reveal": {"startMs": 0, "durationMs": 4000}}],
                    }
                ),
                encoding="utf-8",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["narration"] = [
                {
                    "id": "cue-1",
                    "sceneId": "scene-01",
                    "text": "Món ăn thứ nhất.",
                    "elementIds": ["food-1"],
                }
            ]
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            project = load_project(root)
            self.assertEqual(len(project.narration_cues), 1)
            self.assertEqual(project.narration_cues[0].element_ids, ["food-1"])

    def test_loads_pen_brand(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["penBrand"] = "Ăn dặm mẹ Dâu"
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            project = load_project(root)
            self.assertEqual(project.pen_brand, "Ăn dặm mẹ Dâu")

    def test_rejects_long_pen_brand(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["penBrand"] = "x" * 41
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ProjectError, "40 ký tự"):
                load_project(root)

    def test_rejects_missing_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            (root / "scene.png").unlink()
            with self.assertRaisesRegex(ProjectError, "Không tìm thấy ảnh"):
                load_project(manifest)

    def test_rejects_path_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["scenes"][0]["image"] = "../secret.png"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ProjectError, "đi ra ngoài"):
                load_project(manifest)

    def test_loads_nested_zip_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            make_project(source)
            archive = root / "project.zip"
            with zipfile.ZipFile(archive, "w") as output:
                for file in source.iterdir():
                    output.write(file, f"package/{file.name}")
            project = load_project(archive)
            temporary_root = project.temporary_root
            self.assertIsNotNone(temporary_root)
            self.assertEqual(project.title, "Bữa ăn cho bé")
            project.close()
            self.assertFalse(temporary_root.exists())

    def test_rejects_unsafe_zip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../project.json", "{}")
            with self.assertRaisesRegex(ProjectError, "không an toàn"):
                load_project(archive)


if __name__ == "__main__":
    unittest.main()
