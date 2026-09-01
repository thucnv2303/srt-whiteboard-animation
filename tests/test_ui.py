import unittest
from unittest.mock import Mock, patch

from whiteboard_app.ui import WhiteboardApp, responsive_layout


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


if __name__ == "__main__":
    unittest.main()
