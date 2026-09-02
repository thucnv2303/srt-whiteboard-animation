import unittest
import wave

from whiteboard_app.video_player import format_media_time, pcm_offset, wav_tail_buffer


class VideoPlayerTests(unittest.TestCase):
    def test_formats_player_time(self) -> None:
        self.assertEqual(format_media_time(0), "00:00")
        self.assertEqual(format_media_time(65.2), "01:05")

    def test_pcm_seek_offset_stays_on_sample_boundary(self) -> None:
        pcm_length = 24000 * 2 * 10
        self.assertEqual(pcm_offset(2.5, 24000, 1, 2, pcm_length), 120000)
        self.assertEqual(pcm_offset(99, 24000, 1, 2, pcm_length), pcm_length)

    def test_seek_audio_keeps_wav_header_and_original_sample_rate(self) -> None:
        pcm = b"\0\0" * 24000 * 4
        buffer = wav_tail_buffer(pcm, 1.5, 24000, 1, 2)
        with wave.open(buffer, "rb") as audio:
            self.assertEqual(audio.getframerate(), 24000)
            self.assertEqual(audio.getnchannels(), 1)
            self.assertEqual(audio.getsampwidth(), 2)
            self.assertEqual(audio.getnframes(), 24000 * 2.5)


if __name__ == "__main__":
    unittest.main()
