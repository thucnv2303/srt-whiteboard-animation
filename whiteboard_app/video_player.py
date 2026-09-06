from __future__ import annotations

import io
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


def wav_tail_buffer(
    pcm: bytes,
    seconds: float,
    frame_rate: int,
    channels: int,
    sample_width: int,
) -> io.BytesIO:
    """Gói phần PCM cần phát vào WAV có header để SDL tự resample đúng tốc độ."""
    offset = pcm_offset(seconds, frame_rate, channels, sample_width, len(pcm))
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(channels)
        target.setsampwidth(sample_width)
        target.setframerate(frame_rate)
        target.writeframes(pcm[offset:])
    output.seek(0)
    return output


def preview_frame_interval(source_fps: float, max_preview_fps: float = 30.0) -> float:
    """Nhịp preview tối đa 30 FPS; file kết quả vẫn giữ nguyên FPS nguồn."""
    safe_source = source_fps if source_fps > 0 else 25.0
    return 1.0 / max(1.0, min(safe_source, max_preview_fps))


def fit_video_size(
    source_width: int,
    source_height: int,
    available_width: int,
    available_height: int,
) -> tuple[int, int]:
    """Tính kích thước preview đúng tỷ lệ và không phóng lớn quá ảnh nguồn."""
    if source_width <= 0 or source_height <= 0:
        return max(2, available_width), max(2, available_height)
    scale = min(
        1.0,
        max(2, available_width) / source_width,
        max(2, available_height) / source_height,
    )
    width = max(2, round(source_width * scale))
    height = max(2, round(source_height * scale))
    return width, height


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
        self._wave_buffer: io.BytesIO | None = None

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
            # Thiết bị Windows thường chạy 48 kHz stereo. WAV header bên dưới giúp
            # SDL resample từ nguồn 24 kHz mono, tránh phát nhanh/méo như raw buffer.
            expected = (48000, -16, 2)
            if pygame.mixer.get_init() != expected:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                pygame.mixer.init(frequency=48000, size=-16, channels=2)
        except Exception as exc:
            self.pcm = b""
            raise VideoPlaybackError(f"Không khởi tạo được âm thanh nội bộ: {exc}") from exc
        self.path = path
        return True

    def play_from(self, seconds: float) -> None:
        if not self.pcm or self._pygame is None:
            return
        self.stop()
        self._wave_buffer = wav_tail_buffer(
            self.pcm, seconds, self.frame_rate, self.channels, self.sample_width
        )
        if self._wave_buffer.getbuffer().nbytes <= 44:
            return
        self._sound = self._pygame.mixer.Sound(file=self._wave_buffer)
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
        self._wave_buffer = None

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
        self._current_frame: Any = None
        self._photo: Any = None
        self._canvas_item: Any = None
        self._after_id: str | None = None
        self._pending_frame: tuple[Any, float] | None = None
        self._clock_started = 0.0
        self._preview_interval = 1.0 / 25.0
        self._last_presented_time = -1.0
        self._last_position_notify = 0.0
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
            self._preview_interval = preview_frame_interval(float(self._stream.average_rate or 25))
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
        if self._current_frame is None:
            return
        try:
            from PIL import ImageTk

            width = max(80, self.canvas.winfo_width() - 8)
            height = max(80, self.canvas.winfo_height() - 8)
            target_width, target_height = fit_video_size(
                self._current_frame.width,
                self._current_frame.height,
                width,
                height,
            )
            # Libswscale thực hiện resize trong mã native nhanh hơn đáng kể so với
            # copy + LANCZOS bằng Pillow trên UI thread cho từng frame 60 FPS.
            image = self._current_frame.reformat(
                width=target_width,
                height=target_height,
                format="rgb24",
            ).to_image()
            self._photo = ImageTk.PhotoImage(image)
            self.canvas.configure(background="#101418")
            center = (self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2)
            try:
                if self._canvas_item is None:
                    raise RuntimeError("Chưa có canvas item")
                self.canvas.itemconfigure(self._canvas_item, image=self._photo)
                self.canvas.coords(self._canvas_item, *center)
            except Exception:
                self.canvas.delete("all")
                self._canvas_item = self.canvas.create_image(
                    *center, image=self._photo, anchor="center"
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
        self._current_frame = None
        self._photo = None
        self._canvas_item = None
        self._pending_frame = None
        self._last_presented_time = -1.0
        self._last_position_notify = 0.0

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
                self._current_frame = frame
                self._last_presented_time = frame_time
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
        self._preview_interval = preview_frame_interval(float(self._stream.average_rate or 25))
        if target > 0:
            offset = int(target / float(self._stream.time_base))
            self._container.seek(offset, stream=self._stream, backward=True, any_frame=False)
        self._frames = self._container.decode(self._stream)
        self._pending_frame = None
        self._last_presented_time = target - self._preview_interval
        self._decode_until(target)

    def _queue_next(self) -> None:
        if self.state != "playing" or self._after_id:
            return
        try:
            if self._pending_frame is None:
                current = time.monotonic() - self._clock_started
                minimum_time = max(
                    current - 0.04,
                    self._last_presented_time + self._preview_interval,
                )
                # Video nguồn thường là 60 FPS nhưng Tk chỉ cần tối đa 30 FPS để
                # xem mượt. Vẫn decode tuần tự để giữ seek/GOP đúng, chỉ không đẩy
                # các frame trung gian qua Pillow và Tcl/Tk.
                for _ in range(240):
                    frame = next(self._frames)
                    frame_time = self._frame_time(frame)
                    self._pending_frame = (frame, frame_time)
                    if frame_time + 0.002 >= minimum_time:
                        break
            current = time.monotonic() - self._clock_started
            # Video đầu ra có thể là 60 fps trong khi Tkinter chỉ vẽ ổn định khoảng
            # 25–30 fps. Bỏ toàn bộ frame đã trễ thay vì phát bù khiến hình tụt sau tiếng.
            for _ in range(240):
                _, frame_time = self._pending_frame
                current = time.monotonic() - self._clock_started
                if frame_time >= current - 0.04:
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
        self._current_frame = frame
        self._last_presented_time = frame_time
        self.position = min(self.duration, max(0.0, frame_time))
        self.redraw()
        now = time.monotonic()
        if now - self._last_position_notify >= 0.2:
            self._last_position_notify = now
            self.on_position(self.position, self.duration)
        self._queue_next()

    def _finish(self) -> None:
        self._cancel_tick()
        self._audio.stop()
        self.position = self.duration
        self.state = "ended"
        self.on_position(self.position, self.duration)
        self.on_state(self.state)
