import unittest
from unittest.mock import Mock, patch

from whiteboard_app.voice import VoiceSettings
from whiteboard_app.voice_dialog import VoiceManagerDialog


class VoiceManagerDialogTests(unittest.TestCase):
    def test_typed_cli_path_is_persisted(self) -> None:
        dialog = object.__new__(VoiceManagerDialog)
        dialog.cli_path = Mock()
        dialog.cli_path.get.return_value = r"C:\Python311\Scripts\omnivoice-infer.exe"
        dialog.status_text = Mock()
        dialog.on_log = Mock()

        settings_class = Mock()
        settings_class.load.return_value = VoiceSettings(
            cli_path="old.exe", selected_profile_id="voice-01"
        )
        with patch("whiteboard_app.voice_dialog.VoiceSettings", settings_class):
            dialog._save_cli_settings()

        settings_class.assert_called_once_with(
            cli_path=r"C:\Python311\Scripts\omnivoice-infer.exe",
            selected_profile_id="voice-01",
        )
        settings_class.return_value.save.assert_called_once_with()
        dialog.status_text.set.assert_called_once()


if __name__ == "__main__":
    unittest.main()
