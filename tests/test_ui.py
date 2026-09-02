import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from whiteboard_app.project import load_project
from whiteboard_app.ui import WhiteboardApp, project_preview_items, responsive_layout


class FileDialogTests(unittest.TestCase):
    def test_cancel_file_dialog_does_not_open_another_dialog(self) -> None:
        fake_app = Mock()
        with (
            patch("whiteboard_app.ui.filedialog.askopenfilename", return_value="") as open_file,
            patch("whiteboard_app.ui.filedialog.askdirectory") as open_folder,
        ):
            WhiteboardApp._choose_project_file(fake_app)
        open_file.assert_called_once()
        open_folder.assert_not_called()
        fake_app._open_project.assert_not_called()

    def test_file_selection_is_opened_once(self) -> None:
        fake_app = Mock()
        selected = r"E:\Project AI\Tạo video vẽ tay\examples\project.json"
        with patch("whiteboard_app.ui.filedialog.askopenfilename", return_value=selected):
            WhiteboardApp._choose_project_file(fake_app)
        fake_app._open_project.assert_called_once_with(selected)


class ResponsiveLayoutTests(unittest.TestCase):
    def test_desktop_width_uses_horizontal_layout(self) -> None:
        self.assertEqual(responsive_layout(1280), "horizontal")

    def test_small_window_stacks_settings(self) -> None:
        self.assertEqual(responsive_layout(800), "stacked")


class PreviewItemTests(unittest.TestCase):
    def test_each_narration_cue_becomes_a_visible_content_scene(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "board.png").write_bytes(b"png")
            (root / "board.annotation.json").write_text(
                json.dumps(
                    {
                        "elements": [
                            {"id": "dish-1", "label": "Cháo bò", "region": {"x": 10, "y": 20, "width": 100, "height": 80}},
                            {"id": "dish-2", "label": "Bò bông cải", "region": {"x": 130, "y": 20, "width": 90, "height": 80}},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (root / "project.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "title": "Hai món",
                        "narration": [
                            {"id": "cue-1", "sceneId": "board", "text": "Món một.", "elementIds": ["dish-1"]},
                            {"id": "cue-2", "sceneId": "board", "text": "Món hai.", "elementIds": ["dish-2"]},
                        ],
                        "scenes": [
                            {"id": "board", "image": "board.png", "annotation": "board.annotation.json"}
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            items = project_preview_items(load_project(root))
            self.assertEqual([item.title for item in items], ["Cháo bò", "Bò bông cải"])
            self.assertEqual(items[0].region, (10, 20, 110, 100))
            self.assertEqual(items[1].scene.scene_id, "board")


if __name__ == "__main__":
    unittest.main()
