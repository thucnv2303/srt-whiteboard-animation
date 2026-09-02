from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .project import ProjectError, VideoProject, load_project
from .renderer import RenderError, create_video_poster, create_video_preview_audio, run_pipeline
from .timeline import TimelineError, compile_timeline
from .voice import OmniVoiceError, generate_clone_voice, generate_cue_voices


WAITING = "WAITING"
QUEUED = "QUEUED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
CANCELED = "CANCELED"

WAITING_STATES = (WAITING, QUEUED)
TERMINAL_STATES = (COMPLETED, FAILED, CANCELED)


def jobs_database_path() -> Path:
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / "NetChuyenDong" / "jobs.db"


def shared_runs_dir() -> Path:
    return jobs_database_path().parent / "runs"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class VideoJob:
    job_id: str
    source_path: Path
    title: str
    status: str
    phase: str
    progress: int
    duration_seconds: float
    output_dir: Path
    aspect_ratio: str
    pen_brand: str
    voice_profile_id: str
    voice_name: str
    voice_audio_path: Path | None
    cli_path: str
    error: str
    result_path: Path | None
    poster_path: Path | None
    preview_audio_path: Path | None
    position: int
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "VideoJob":
        def optional_path(value: object) -> Path | None:
            text = str(value or "").strip()
            return Path(text) if text else None

        return cls(
            job_id=str(row["job_id"]),
            source_path=Path(str(row["source_path"])),
            title=str(row["title"]),
            status=str(row["status"]),
            phase=str(row["phase"]),
            progress=int(row["progress"]),
            duration_seconds=float(row["duration_seconds"]),
            output_dir=Path(str(row["output_dir"])),
            aspect_ratio=str(row["aspect_ratio"]),
            pen_brand=str(row["pen_brand"]),
            voice_profile_id=str(row["voice_profile_id"]),
            voice_name=str(row["voice_name"]),
            voice_audio_path=optional_path(row["voice_audio_path"]),
            cli_path=str(row["cli_path"]),
            error=str(row["error"]),
            result_path=optional_path(row["result_path"]),
            poster_path=optional_path(row["poster_path"]),
            preview_audio_path=optional_path(row["preview_audio_path"]),
            position=int(row["position"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class JobResult:
    video: Path
    poster: Path | None
    preview_audio: Path | None
    duration_seconds: float


class JobStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or jobs_database_path()).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    phase TEXT NOT NULL DEFAULT '',
                    progress INTEGER NOT NULL DEFAULT 0,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    output_dir TEXT NOT NULL,
                    aspect_ratio TEXT NOT NULL,
                    pen_brand TEXT NOT NULL DEFAULT '',
                    voice_profile_id TEXT NOT NULL DEFAULT '',
                    voice_name TEXT NOT NULL DEFAULT '',
                    voice_audio_path TEXT NOT NULL DEFAULT '',
                    cli_path TEXT NOT NULL DEFAULT '',
                    error TEXT NOT NULL DEFAULT '',
                    result_path TEXT NOT NULL DEFAULT '',
                    poster_path TEXT NOT NULL DEFAULT '',
                    preview_audio_path TEXT NOT NULL DEFAULT '',
                    position INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_status_position
                    ON jobs(status, position);
                CREATE TABLE IF NOT EXISTS job_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_job_logs_job
                    ON job_logs(job_id, log_id);
                """
            )

    def add(
        self,
        source_path: Path,
        project: VideoProject,
        aspect_ratio: str,
        pen_brand: str,
        voice_profile_id: str,
        voice_name: str,
        voice_audio_path: Path | None,
        cli_path: str,
        output_dir: Path | None = None,
    ) -> VideoJob:
        job_id = uuid.uuid4().hex
        if output_dir is None:
            base = project.root / "output" / "runs" if project.temporary_root is None else shared_runs_dir()
            output_dir = base / job_id
        timestamp = now_iso()
        duration = sum(scene.duration_ms for scene in project.scenes) / 1000
        with self._connect() as connection:
            position = int(connection.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM jobs").fetchone()[0])
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, source_path, title, status, phase, progress, duration_seconds,
                    output_dir, aspect_ratio, pen_brand, voice_profile_id, voice_name,
                    voice_audio_path, cli_path, error, result_path, poster_path,
                    preview_audio_path, position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, '', 0, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', '', ?, ?, ?)
                """,
                (
                    job_id,
                    str(source_path.resolve()),
                    project.title,
                    WAITING,
                    duration,
                    str(output_dir.resolve()),
                    aspect_ratio,
                    pen_brand,
                    voice_profile_id,
                    voice_name,
                    str(voice_audio_path.resolve()) if voice_audio_path else "",
                    cli_path,
                    position,
                    timestamp,
                    timestamp,
                ),
            )
        self.append_log(job_id, "Đã thêm dự án vào hàng đợi.")
        job = self.get(job_id)
        assert job is not None
        return job

    def get(self, job_id: str) -> VideoJob | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return VideoJob.from_row(row) if row else None

    def list(self, statuses: Iterable[str] | None = None) -> list[VideoJob]:
        parameters: tuple[object, ...] = ()
        sql = "SELECT * FROM jobs"
        if statuses:
            values = tuple(statuses)
            sql += f" WHERE status IN ({','.join('?' for _ in values)})"
            parameters = values
        sql += " ORDER BY position, created_at"
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [VideoJob.from_row(row) for row in rows]

    def counts(self) -> dict[str, int]:
        counts = {"total": 0, "running": 0, "waiting": 0, "completed": 0, "failed": 0}
        with self._connect() as connection:
            rows = connection.execute("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status").fetchall()
        for row in rows:
            status, count = str(row["status"]), int(row["count"])
            counts["total"] += count
            if status == RUNNING:
                counts["running"] += count
            elif status in WAITING_STATES:
                counts["waiting"] += count
            elif status == COMPLETED:
                counts["completed"] += count
            elif status == FAILED:
                counts["failed"] += count
        return counts

    def queue(self, job_ids: Iterable[str]) -> int:
        values = tuple(dict.fromkeys(job_ids))
        if not values:
            return 0
        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE jobs SET status = ?, phase = 'Đang chờ', updated_at = ? "
                f"WHERE job_id IN ({','.join('?' for _ in values)}) AND status = ?",
                (QUEUED, now_iso(), *values, WAITING),
            )
        return cursor.rowcount

    def queue_all_waiting(self) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE jobs SET status = ?, phase = 'Đang chờ', updated_at = ? WHERE status = ?",
                (QUEUED, now_iso(), WAITING),
            )
        return cursor.rowcount

    def next_queued(self) -> VideoJob | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY position, created_at LIMIT 1",
                (QUEUED,),
            ).fetchone()
        return VideoJob.from_row(row) if row else None

    def update_progress(self, job_id: str, phase: str, progress: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET phase = ?, progress = ?, updated_at = ? WHERE job_id = ?",
                (phase, max(0, min(100, int(progress))), now_iso(), job_id),
            )

    def mark_running(self, job_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET status = ?, phase = 'Đang kiểm tra', progress = 1, error = '', updated_at = ? "
                "WHERE job_id = ?",
                (RUNNING, now_iso(), job_id),
            )

    def mark_completed(self, job_id: str, result: JobResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE jobs SET status = ?, phase = 'Hoàn tất', progress = 100,
                    duration_seconds = ?, result_path = ?, poster_path = ?,
                    preview_audio_path = ?, error = '', updated_at = ?
                WHERE job_id = ?
                """,
                (
                    COMPLETED,
                    result.duration_seconds,
                    str(result.video),
                    str(result.poster or ""),
                    str(result.preview_audio or ""),
                    now_iso(),
                    job_id,
                ),
            )

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET status = ?, phase = 'Lỗi', error = ?, updated_at = ? WHERE job_id = ?",
                (FAILED, error, now_iso(), job_id),
            )

    def mark_canceled(self, job_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET status = ?, phase = 'Đã hủy', updated_at = ? "
                "WHERE job_id = ? AND status != ?",
                (CANCELED, now_iso(), job_id, COMPLETED),
            )

    def retry(self, job_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE jobs SET status = ?, phase = '', progress = 0, error = '', updated_at = ? "
                "WHERE job_id = ? AND status IN (?, ?)",
                (WAITING, now_iso(), job_id, FAILED, CANCELED),
            )
        if cursor.rowcount:
            self.append_log(job_id, "Đã đưa job về trạng thái chờ để chạy lại.")
        return bool(cursor.rowcount)

    def recover_interrupted(self) -> int:
        message = "App đã đóng khi job đang chạy. Hãy bấm Chạy lại để tiếp tục."
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE jobs SET status = ?, phase = 'Bị gián đoạn', error = ?, updated_at = ? "
                "WHERE status = ?",
                (FAILED, message, now_iso(), RUNNING),
            )
        return cursor.rowcount

    def delete(self, job_ids: Iterable[str]) -> int:
        values = tuple(dict.fromkeys(job_ids))
        if not values:
            return 0
        with self._connect() as connection:
            cursor = connection.execute(
                f"DELETE FROM jobs WHERE job_id IN ({','.join('?' for _ in values)}) "
                "AND status != ?",
                (*values, RUNNING),
            )
        return cursor.rowcount

    def append_log(self, job_id: str, message: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO job_logs(job_id, created_at, message) VALUES (?, ?, ?)",
                (job_id, now_iso(), message),
            )

    def logs(self, job_id: str, limit: int = 300) -> list[tuple[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT created_at, message FROM job_logs WHERE job_id = ? "
                "ORDER BY log_id DESC LIMIT ?",
                (job_id, max(1, limit)),
            ).fetchall()
        return [(str(row["created_at"]), str(row["message"])) for row in reversed(rows)]


def execute_video_job(
    job: VideoJob,
    cancel_event: threading.Event,
    on_progress: Callable[[str, int], None],
    on_log: Callable[[str], None],
) -> JobResult:
    project: VideoProject | None = None
    try:
        on_progress("Đang kiểm tra dự án", 3)
        project = load_project(job.source_path)
        project.pen_brand = job.pen_brand or None
        output_dir = job.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        text = project.script_text.strip() or " ".join(cue.text for cue in project.narration_cues)
        needs_voice = bool(project.narration_cues or text) and not project.voice
        if needs_voice and (not job.cli_path or not job.voice_audio_path):
            raise OmniVoiceError("Job chưa có cấu hình OmniVoice hoặc giọng mẫu.")

        duration_seconds = sum(scene.duration_ms for scene in project.scenes) / 1000
        if project.narration_cues:
            assert job.voice_audio_path is not None
            on_progress("Đang tạo voice", 10)
            cue_audio = generate_cue_voices(
                cli_path=job.cli_path,
                cues=project.narration_cues,
                reference_audio=job.voice_audio_path,
                output_dir=output_dir / "audio-cues",
                on_log=on_log,
                cancel_event=cancel_event,
            )
            on_progress("Đang đồng bộ timeline", 38)
            timeline = compile_timeline(project, cue_audio, output_dir, on_log)
            project.voice = timeline.voice_path
            project.runtime_annotations = timeline.runtime_annotations
            duration_seconds = timeline.total_duration_ms / 1000
        elif text and not project.voice:
            assert job.voice_audio_path is not None
            on_progress("Đang tạo voice", 10)
            project.voice = generate_clone_voice(
                cli_path=job.cli_path,
                text=text,
                reference_audio=job.voice_audio_path,
                output=output_dir / "voice-clone.wav",
                on_log=on_log,
                cancel_event=cancel_event,
            )

        on_progress("Đang dựng video", 45)

        def render_progress(index: int, total: int, label: str) -> None:
            fraction = index / max(1, total)
            on_progress(label, 45 + round(fraction * 45))

        result = run_pipeline(
            project,
            output_dir,
            on_log,
            cancel_event,
            aspect_ratio=job.aspect_ratio,
            on_progress=render_progress,
        )
        on_progress("Đang tạo preview", 94)
        poster = create_video_poster(result, output_dir / "preview.jpg", on_log)
        preview_audio = create_video_preview_audio(result, output_dir / "preview-audio.wav", on_log)
        return JobResult(result, poster, preview_audio, duration_seconds)
    finally:
        if project:
            project.close()


class SequentialJobRunner:
    def __init__(
        self,
        store: JobStore,
        on_event: Callable[[str, str, object], None] | None = None,
        executor: Callable[
            [VideoJob, threading.Event, Callable[[str, int], None], Callable[[str], None]],
            JobResult,
        ] = execute_video_job,
    ) -> None:
        self.store = store
        self.on_event = on_event or (lambda _kind, _job_id, _payload: None)
        self.executor = executor
        self.paused = False
        self.active_job_id: str | None = None
        self._active_cancel = threading.Event()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self.store.recover_interrupted()
        self._thread = threading.Thread(target=self._run, name="video-job-runner", daemon=True)
        self._thread.start()

    def queue(self, job_ids: Iterable[str]) -> int:
        count = self.store.queue(job_ids)
        if count:
            self._wake.set()
            self.on_event("queue", "", count)
        return count

    def queue_all(self) -> int:
        count = self.store.queue_all_waiting()
        if count:
            self._wake.set()
            self.on_event("queue", "", count)
        return count

    def set_paused(self, paused: bool) -> None:
        self.paused = paused
        if not paused:
            self._wake.set()
        self.on_event("paused", "", paused)

    def cancel(self, job_id: str) -> bool:
        job = self.store.get(job_id)
        if not job or job.status == COMPLETED:
            return False
        if self.active_job_id == job_id:
            self._active_cancel.set()
        else:
            self.store.mark_canceled(job_id)
            self.store.append_log(job_id, "Job đã bị hủy trước khi chạy.")
            self.on_event("changed", job_id, CANCELED)
        return True

    def stop(self) -> None:
        self._stop.set()
        self._active_cancel.set()
        self._wake.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            if self.paused:
                self._wake.wait(0.5)
                self._wake.clear()
                continue
            job = self.store.next_queued()
            if job is None:
                self._wake.wait(0.5)
                self._wake.clear()
                continue
            self.active_job_id = job.job_id
            self._active_cancel = threading.Event()
            self.store.mark_running(job.job_id)
            self.store.append_log(job.job_id, "Bắt đầu xử lý job.")
            self.on_event("changed", job.job_id, RUNNING)

            def progress(phase: str, value: int) -> None:
                self.store.update_progress(job.job_id, phase, value)
                self.on_event("progress", job.job_id, (phase, value))

            def log(message: str) -> None:
                if message:
                    self.store.append_log(job.job_id, message)
                    self.on_event("log", job.job_id, message)

            try:
                result = self.executor(job, self._active_cancel, progress, log)
                if self._active_cancel.is_set():
                    self.store.mark_canceled(job.job_id)
                    self.store.append_log(job.job_id, "Job đã bị hủy.")
                    self.on_event("changed", job.job_id, CANCELED)
                else:
                    self.store.mark_completed(job.job_id, result)
                    self.store.append_log(job.job_id, f"Hoàn tất: {result.video}")
                    self.on_event("completed", job.job_id, result)
            except (ProjectError, OmniVoiceError, TimelineError, RenderError, OSError) as exc:
                if self._active_cancel.is_set():
                    self.store.mark_canceled(job.job_id)
                    self.store.append_log(job.job_id, "Job đã bị hủy.")
                    self.on_event("changed", job.job_id, CANCELED)
                else:
                    self.store.mark_failed(job.job_id, str(exc))
                    self.store.append_log(job.job_id, f"LỖI: {exc}")
                    self.on_event("failed", job.job_id, str(exc))
            except Exception as exc:  # Không để một job lỗi làm chết toàn worker.
                self.store.mark_failed(job.job_id, f"Lỗi không xác định: {exc}")
                self.store.append_log(job.job_id, f"LỖI KHÔNG XÁC ĐỊNH: {exc}")
                self.on_event("failed", job.job_id, str(exc))
            finally:
                self.active_job_id = None
                self.on_event("idle", job.job_id, None)

