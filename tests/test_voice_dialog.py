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

    def test_save_selected_reference_text_updates_library(self) -> None:
        from pathlib import Path
        from whiteboard_app.voice import VoiceLibrary, VoiceProfile

        profile = VoiceProfile(
            profile_id="p-1",
            name="Test Voice",
            audio_path=Path("test.wav"),
            source_path=Path("source.wav"),
            duration_seconds=5.0,
            quality_score=95,
            snr_db=20.0,
            reference_text="Ban đầu",
        )
        library = Mock(spec=VoiceLibrary)
        library.profiles = [profile]
        library.get.return_value = profile

        dialog = object.__new__(VoiceManagerDialog)
        dialog.library = library
        dialog.profile_tree = Mock()
        dialog.profile_tree.selection.return_value = ("p-1",)
        dialog.selected_ref_text = Mock()
        dialog.selected_ref_text.get.return_value = "Văn bản mới đã cập nhật"
        dialog.on_log = Mock()
        dialog.status_text = Mock()
        dialog.on_library_changed = Mock()

        dialog._save_selected_reference_text()

        self.assertEqual(library.profiles[0].reference_text, "Văn bản mới đã cập nhật")
        library.save.assert_called_once()
        dialog.on_library_changed.assert_called_once()

    @patch("whiteboard_app.voice_dialog.messagebox.askyesno", return_value=True)
    def test_delete_selected_removes_profile_after_confirmation(self, mock_askyesno: Mock) -> None:
        from pathlib import Path
        from whiteboard_app.voice import VoiceLibrary, VoiceProfile

        profile = VoiceProfile(
            profile_id="p-del",
            name="Delete Me",
            audio_path=Path("del.wav"),
            source_path=Path("source.wav"),
            duration_seconds=3.0,
            quality_score=90,
            snr_db=20.0,
        )
        library = Mock(spec=VoiceLibrary)
        library.get.return_value = profile

        dialog = object.__new__(VoiceManagerDialog)
        dialog.library = library
        dialog.profile_tree = Mock()
        dialog.profile_tree.selection.return_value = ("p-del",)
        dialog.on_log = Mock()
        dialog.status_text = Mock()
        dialog.on_library_changed = Mock()
        dialog._refresh_profiles = Mock()

        dialog._delete_selected()

        mock_askyesno.assert_called_once()
        library.delete_profile.assert_called_once_with("p-del")
        dialog._refresh_profiles.assert_called_once()
        dialog.on_library_changed.assert_called_once()


if __name__ == "__main__":
    unittest.main()
