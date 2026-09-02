from __future__ import annotations

import time
import wave
from pathlib import Path
from typing import Any, Callable


class VideoPlaybackError(RuntimeError):
    """Lỗi phát video có thể hiển thị trực tiếp trong giao diện."""


def format_media_time(seconds: float) -> str:
    total = max(0, round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def pcm_offset(
    seconds: float,
    frame_rate: int,
    channels: int,
    sample_width: int,
    pcm_length: int,
) -> int:
    bytes_per_frame = max(1, channels * sample_width)
    requested = max(0, round(seconds * frame_rate)) * bytes_per_frame
    available = pcm_length - (pcm_length % bytes_per_frame)
    return min(requested, available)


class WaveAudioTrack:
    def __init__(self) -> None:
        self.path: Path | None = None
        self.frame_rate = 24000
        self.channels = 1
        self.sample_width = 2
        self.pcm = b""
        self._pygame: Any = None
        self._sound: Any = None
        self._channel: Any = None

    def load(self, path: Path | None) -> bool:
        self.close()
        if path is None or not path.is_file():
            return False
        try:
            with wave.open(str(path), "rb") as source:
                self.frame_rate = source.getframerate()
                self.channels = source.getnchannels()
                self.sample_width = source.getsampwidth()
                self.pcm = source.readframes(source.getnframes())
        except (OSError, wave.Error) as exc:
            raise VideoPlaybackError(f"Không đọc được âm thanh preview: {exc}") from exc
        if self.sample_width != 2 or self.channels not in (1, 2):
            raise VideoPlaybackError("Âm thanh preview phải là WAV PCM 16-bit mono hoặc stereo.")
        try:
            import pygame

            self._pygame = pygame
            expected = (self.frame_rate, -16, self.channels)
            if pygame.mixer.get_init() != expected:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                pygame.mixer.init(frequency=self.frame_rate, size=-16, channels=self.channels)
        except Exception as exc:
            self.pcm = b""
            raise VideoPlaybackError(f"Không khởi tạo được âm thanh nội bộ: {exc}") from exc
        self.path = path
        return True

    def play_from(self, seconds: float) -> None:
        if not self.pcm or self._pygame is None:
            return
        self.stop()
        offset = pcm_offset(
            seconds, self.frame_rate, self.channels, self.sample_width, len(self.pcm)
        )
        if offset >= len(self.pcm):
            return
        self._sound = self._pygame.mixer.Sound(buffer=self.pcm[offset:])
        self._channel = self._sound.play()

    def pause(self) -> None:
        if self._channel is not None:
            self._channel.pause()

    def resume(self) -> None:
        if self._channel is not None:
            self._channel.unpause()

    def stop(self) -> None:
        if self._channel is not None:
            self._channel.stop()
        self._channel = None
        self._sound = None

    def close(self) -> None:
        self.stop()
        self.path = None
        self.pcm = b""


class TkVideoPlayer:
    """Trình phát MP4 tối giản: PyAV giải mã hình, pygame phát WAV đồng bộ."""

    def __init__(
        self,
        owner: Any,
        canvas: Any,
        on_position: Callable[[float, float], None],
        on_state: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.owner = owner
        self.canvas = canvas
        self.on_position = on_position
        self.on_state = on_state
        self.on_error = on_error
        self.path: Path | None = None
        self.duration = 0.0
        self.position = 0.0
        self.state = "empty"
        self._container: Any = None
        self._stream: Any = None
        self._frames: Any = None
        self._current_image: Any = None
        self._photo: Any = None
        self._after_id: str | None = None
        self._pending_frame: tuple[Any, float] | None = None
        self._clock_started = 0.0
        self._audio = WaveAudioTrack()
        self._audio_available = False

    @property
    def loaded(self) -> bool:
        return self.path is not None and self._container is not None

    def load(self, path: Path, audio_path: Path | None = None) -> None:
        self.close()
        if not path.is_file():
            raise VideoPlaybackError(f"Không tìm thấy video: {path}")
        try:
            import av
        except ImportError as exc:
            raise VideoPlaybackError("Thiếu PyAV. Hãy chạy lại run_app.bat để bổ sung dependency.") from exc
        try:
            self.path = path
            self._container = av.open(str(path))
            self._stream = self._container.streams.video[0]
            self._stream.thread_type = "AUTO"
            if self._stream.duration is not None:
                self.duration = float(self._stream.duration * self._stream.time_base)
            elif self._container.duration is not None:
                self.duration = float(self._container.duration / av.time_base)
            else:
                self.duration = 0.0
            self._frames = self._container.decode(self._stream)
            self._audio_available = self._audio.load(audio_path) if audio_path else False
            self._decode_until(0.0)
            self.position = 0.0
            self.state = "ready"
            self.on_position(0.0, self.duration)
            self.on_state(self.state)
        except VideoPlaybackError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise VideoPlaybackError(f"Không mở được video trong app: {exc}") from exc

    def play_pause(self) -> None:
        if not self.loaded:
            return
        if self.state == "playing":
            self.pause()
        else:
            self.play()

    def play(self) -> None:
        if not self.loaded:
            return
        if self.duration and self.position >= self.duration - 0.05:
            self.seek(0.0)
        was_paused = self.state == "paused"
        self.state = "playing"
        self._clock_started = time.monotonic() - self.position
        if self._audio_available:
            self._audio.resume() if was_paused else self._audio.play_from(self.position)
        self.on_state(self.state)
        self._queue_next()

    def pause(self) -> None:
        if self.state != "playing":
            return
        self.position = min(self.duration, max(0.0, time.monotonic() - self._clock_started))
        if self._after_id:
            self.owner.after_cancel(self._after_id)
            self._after_id = None
        self._audio.pause()
        self.state = "paused"
        self.on_position(self.position, self.duration)
        self.on_state(self.state)

    def stop(self) -> None:
        if not self.loaded:
            return
        self._cancel_tick()
        self._audio.stop()
        self.seek(0.0)
        self.state = "ready"
        self.on_state(self.state)

    def seek(self, seconds: float) -> None:
        if not self.path:
            return
        was_playing = self.state == "playing"
        self._cancel_tick()
        self._audio.stop()
        if self.duration:
            target = min(max(0.0, seconds), max(0.0, self.duration - 0.04))
        else:
            target = max(0.0, seconds)
        try:
            self._open_at(target)
            self.position = target
            self.on_position(self.position, self.duration)
            if was_playing:
                self.state = "playing"
                self._clock_started = time.monotonic() - self.position
                if self._audio_available:
                    self._audio.play_from(self.position)
                self._queue_next()
            else:
                self.state = "paused" if target > 0 else "ready"
            self.on_state(self.state)
        except Exception as exc:
            self.on_error(f"Không tua được video: {exc}")

    def redraw(self) -> None:
        if self._current_image is None:
            return
        try:
            from PIL import Image, ImageTk

            width = max(80, self.canvas.winfo_width() - 8)
            height = max(80, self.canvas.winfo_height() - 8)
            image = self._current_image.copy()
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            self._photo = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            self.canvas.configure(background="#101418")
            self.canvas.create_image(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                image=self._photo,
                anchor="center",
            )
        except Exception as exc:
            self.on_error(f"Không hiển thị được khung hình video: {exc}")

    def close(self) -> None:
        self._cancel_tick()
        self._audio.close()
        if self._container is not None:
            try:
                self._container.close()
            except Exception:
                pass
        self.path = None
        self.duration = 0.0
        self.position = 0.0
        self.state = "empty"
        self._container = None
        self._stream = None
        self._frames = None
        self._current_image = None
        self._photo = None
        self._pending_frame = None

    def _cancel_tick(self) -> None:
        if self._after_id:
            try:
                self.owner.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def _frame_time(self, frame: Any) -> float:
        if frame.pts is None:
            rate = float(self._stream.average_rate or 25)
            return self.position + 1.0 / max(1.0, rate)
        return float(frame.pts * frame.time_base)

    def _decode_until(self, target: float) -> None:
        for frame in self._frames:
            frame_time = self._frame_time(frame)
            if frame_time + 0.04 >= target:
                self._current_image = frame.to_image().convert("RGB")
                self.redraw()
                return
        raise VideoPlaybackError("Video không có khung hình để phát.")

    def _open_at(self, target: float) -> None:
        assert self.path is not None
        import av

        if self._container is not None:
            self._container.close()
        self._container = av.open(str(self.path))
        self._stream = self._container.streams.video[0]
        self._stream.thread_type = "AUTO"
        if target > 0:
            offset = int(target / float(self._stream.time_base))
            self._container.seek(offset, stream=self._stream, backward=True, any_frame=False)
        self._frames = self._container.decode(self._stream)
        self._pending_frame = None
        self._decode_until(target)

    def _queue_next(self) -> None:
        if self.state != "playing" or self._after_id:
            return
        try:
            if self._pending_frame is None:
                frame = next(self._frames)
                self._pending_frame = (frame, self._frame_time(frame))
            current = time.monotonic() - self._clock_started
            # Nếu máy giải mã chậm, bỏ vài frame cũ để hình luôn bám đồng hồ âm thanh.
            for _ in range(8):
                _, frame_time = self._pending_frame
                if frame_time >= current - 0.08:
                    break
                frame = next(self._frames)
                self._pending_frame = (frame, self._frame_time(frame))
            _, frame_time = self._pending_frame
            delay_ms = max(1, round((frame_time - current) * 1000))
            self._after_id = self.owner.after(delay_ms, self._present_pending)
        except StopIteration:
            self._finish()
        except Exception as exc:
            self.on_error(f"Lỗi giải mã video: {exc}")
            self.pause()

    def _present_pending(self) -> None:
        self._after_id = None
        if self.state != "playing" or self._pending_frame is None:
            return
        frame, frame_time = self._pending_frame
        self._pending_frame = None
        self._current_image = frame.to_image().convert("RGB")
        self.position = min(self.duration, max(0.0, frame_time))
        self.redraw()
        self.on_position(self.position, self.duration)
        self._queue_next()

    def _finish(self) -> None:
        self._cancel_tick()
        self._audio.stop()
        self.position = self.duration
        self.state = "ended"
        self.on_position(self.position, self.duration)
        self.on_state(self.state)
