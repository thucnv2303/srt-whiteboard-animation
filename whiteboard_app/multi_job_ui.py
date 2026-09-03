from __future__ import annotations

import os
import queue
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from .jobs import (
    CANCELED,
    COMPLETED,
    EDITABLE_STATES,
    FAILED,
    QUEUED,
    RUNNING,
    WAITING,
    WAITING_STATES,
    JobResult,
    JobStore,
    SequentialJobRunner,
    VideoJob,
)
from .project import ProjectError, load_project
from .preferences import VideoPreferences
from .preview import preview_frame_size
from .renderer import ASPECT_RATIOS
from .video_player import TkVideoPlayer, VideoPlaybackError, format_media_time
from .voice import OmniVoiceError, VoiceLibrary, VoiceProfile, VoiceSettings, play_audio, stop_audio

if TYPE_CHECKING:
    from .ui import WhiteboardApp


FILTERS: dict[str, tuple[str, ...] | None] = {
    "total": None,
    "running": (RUNNING,),
    "waiting": WAITING_STATES,
    "completed": (COMPLETED,),
    "failed": (FAILED,),
}


def job_status_label(status: str) -> str:
    return {
        WAITING: "Đang chờ",
        QUEUED: "Đang chờ",
        RUNNING: "Đang chạy",
        COMPLETED: "Hoàn tất",
        FAILED: "Lỗi",
        CANCELED: "Đã hủy",
    }.get(status, status)


def run_button_label(count: int) -> str:
    return f"▶ Chạy {count} job"


def format_queue_elapsed(elapsed_seconds: float) -> str:
    total = max(0, int(elapsed_seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def running_button_label(count: int, elapsed_seconds: float) -> str:
    return f"● Đang chạy {count} job • {format_queue_elapsed(elapsed_seconds)}"


def preferred_voice_index(
    options: list[tuple[str, str, Path]],
    job_profile_id: str,
    job_voice_name: str,
    default_profile_id: str,
) -> int:
    """Ưu tiên voice của job, sau đó voice mặc định đã lưu trên máy."""
    if job_profile_id:
        match = next(
            (index for index, option in enumerate(options) if option[0] == job_profile_id),
            None,
        )
        if match is not None:
            return match
    if job_voice_name:
        match = next(
            (index for index, option in enumerate(options) if option[1] == job_voice_name),
            None,
        )
        if match is not None:
            return match
    if default_profile_id:
        match = next(
            (index for index, option in enumerate(options) if option[0] == default_profile_id),
            None,
        )
        if match is not None:
            return match
    return 0 if options else -1


def matching_voice_profile(
    profiles: list[VoiceProfile],
    profile_id: str,
    voice_name: str,
    audio_path: Path | None,
) -> VoiceProfile | None:
    """Ghép snapshot voice cũ về profile thư viện ổn định."""
    if profile_id:
        match = next((profile for profile in profiles if profile.profile_id == profile_id), None)
        if match:
            return match
    if audio_path:
        audio_key = str(audio_path.resolve()).casefold()
        match = next(
            (
                profile
                for profile in profiles
                if str(profile.audio_path.resolve()).casefold() == audio_key
            ),
            None,
        )
        if match:
            return match
    if voice_name:
        return next((profile for profile in profiles if profile.name == voice_name), None)
    return None


def settings_button_label(count: int, has_checked_jobs: bool) -> str:
    return f"⚙ Thiết lập {count} job" if has_checked_jobs else "⚙ Thiết lập job"


def job_settings_rows(job: VideoJob) -> list[tuple[str, str]]:
    return [
        ("Giọng đọc", job.voice_name or "Voice có sẵn trong dự án"),
        ("Khung hình", job.aspect_ratio),
        ("Chữ trên bút", job.pen_brand or "Không có"),
        ("Nơi lưu", str(job.output_dir)),
    ]


def job_settings_editable(status: str) -> bool:
    return status in EDITABLE_STATES


def header_checkbox_text(visible_ids: list[str], checked_ids: set[str]) -> str:
    if not visible_ids or not any(job_id in checked_ids for job_id in visible_ids):
        return "☐"
    if all(job_id in checked_ids for job_id in visible_ids):
        return "☑"
    return "▣"


def settings_target_ids(
    jobs: list[VideoJob], checked_ids: set[str], focused_job_id: str | None
) -> list[str]:
    """Ưu tiên toàn bộ checkbox; nếu chưa tích thì dùng job đang xem."""
    selected = [job.job_id for job in jobs if job.job_id in checked_ids]
    if selected:
        return selected
    if focused_job_id and any(job.job_id == focused_job_id for job in jobs):
        return [focused_job_id]
    return []


def bulk_output_directory(output_root: Path, job_id: str) -> Path:
    """Mỗi job luôn có thư mục con riêng khi áp dụng thiết lập hàng loạt."""
    return output_root.resolve() / job_id


def multi_job_layout(width: int) -> str:
    if width >= 1180:
        return "three"
    if width >= 820:
        return "two"
    return "stack"


def open_path(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class MultiJobView(ttk.Frame):
    def __init__(self, app: "WhiteboardApp") -> None:
        super().__init__(app, style="App.TFrame", padding=(18, 14))
        self.app = app
        self.store = JobStore()
        self.events: queue.Queue[tuple[str, str, object]] = queue.Queue()
        self.runner = SequentialJobRunner(self.store, on_event=self._runner_event)
        self.checked_job_ids: set[str] = set()
        self.active_filter = "total"
        self.detail_job_id: str | None = None
        self.detail_aspect_ratio = "16:9"
        self.settings_dialog: tk.Toplevel | None = None
        self.queue_paused = False
        self.batch_started_at: float | None = None
        self.batch_job_count = 0
        self._detail_image = None
        self._detail_photo = None
        self._closed = False

        self.total_kpi = tk.StringVar(value="TỔNG JOB\n0")
        self.running_kpi = tk.StringVar(value="ĐANG CHẠY\n0")
        self.waiting_kpi = tk.StringVar(value="ĐANG CHỜ\n0")
        self.completed_kpi = tk.StringVar(value="HOÀN TẤT\n0")
        self.failed_kpi = tk.StringVar(value="LỖI\n0")
        self.run_selected_text = tk.StringVar(value=run_button_label(0))
        self.pause_text = tk.StringVar(value="Ⅱ Tạm dừng")
        self.detail_title = tk.StringVar(value="Chưa chọn job")
        self.detail_meta = tk.StringVar(value="")
        self.detail_phase = tk.StringVar(value="Chọn một job trong hàng đợi")
        self.detail_progress = tk.IntVar(value=0)
        self.detail_video_time = tk.StringVar(value="00:00 / 00:00")
        self.detail_settings_text = tk.StringVar(value=settings_button_label(0, False))
        self.worker_status = tk.StringVar(value="Worker OmniVoice: sẵn sàng  •  GPU: 1 tác vụ")
        self._workspace_layout = ""

        self._build()
        self.video_player = TkVideoPlayer(
            self,
            self.detail_canvas,
            on_position=self._video_position,
            on_state=self._video_state,
            on_error=self._video_error,
        )
        self.bind("<Configure>", self._on_resize)
        self.after(150, self._poll_events)
        self.refresh()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="Studio video vẽ tay", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="ĐƠN NHIỆM", command=self.app._show_single_mode).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(header, text="MULTI JOB", style="ModeActive.TButton").grid(row=0, column=2)
        ttk.Button(header, text="＋ Thêm dự án", command=self._add_projects).grid(
            row=0, column=3, padx=(14, 6)
        )
        ttk.Button(header, text="▣ Mở thư mục", command=self._open_selected_folder).grid(
            row=0, column=4, padx=(0, 6)
        )
        ttk.Button(
            header, text="▶ Bắt đầu hàng đợi", style="Accent.TButton", command=self._start_all
        ).grid(row=0, column=5)

        kpis = ttk.Frame(self, style="App.TFrame")
        kpis.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        variables = [
            ("total", self.total_kpi),
            ("running", self.running_kpi),
            ("waiting", self.waiting_kpi),
            ("completed", self.completed_kpi),
            ("failed", self.failed_kpi),
        ]
        self.kpi_buttons: dict[str, ttk.Button] = {}
        for column, (key, variable) in enumerate(variables):
            kpis.grid_columnconfigure(column, weight=1)
            button = ttk.Button(
                kpis,
                textvariable=variable,
                style="KPIActive.TButton" if key == "total" else "KPI.TButton",
                command=lambda value=key: self._set_filter(value),
            )
            button.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 5, 0))
            self.kpi_buttons[key] = button

        self.workspace = ttk.Frame(self, style="App.TFrame")
        self.workspace.grid(row=2, column=0, sticky="nsew")
        self.workspace.grid_rowconfigure(0, weight=1)
        self.queue_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=12)
        self.script_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=12)
        self.detail_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=12)
        self._build_queue_card()
        self._build_script_card()
        self._build_detail_card()
        self._apply_workspace_layout("three")

        log_card = ttk.Frame(self, style="Card.TFrame", padding=(12, 9))
        log_card.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        log_card.grid_columnconfigure(0, weight=1)
        ttk.Label(log_card, text="Nhật ký job", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.job_log = tk.Text(
            log_card,
            height=6,
            wrap="word",
            state="disabled",
            relief="flat",
            padx=10,
            pady=7,
            font=("Consolas", 9),
            background="#17202a",
            foreground="#e8edf2",
        )
        self.job_log.grid(row=1, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_card, orient="vertical", command=self.job_log.yview)
        log_scroll.grid(row=1, column=1, sticky="ns")
        self.job_log.configure(yscrollcommand=log_scroll.set)
        ttk.Label(self, textvariable=self.worker_status, style="Subtitle.TLabel").grid(
            row=4, column=0, sticky="w", pady=(8, 0)
        )

    def _build_queue_card(self) -> None:
        self.queue_card.grid_columnconfigure(0, weight=1)
        self.queue_card.grid_rowconfigure(1, weight=1)
        toolbar = ttk.Frame(self.queue_card, style="Card.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        toolbar.grid_columnconfigure(0, weight=1)
        ttk.Label(toolbar, text="Hàng đợi xử lý", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 7)
        )
        self.run_selected_button = ttk.Button(
            toolbar, textvariable=self.run_selected_text, command=self._run_selected
        )
        self.run_selected_button.grid(row=1, column=0, sticky="w", padx=(0, 4))
        self.detail_settings_button = ttk.Button(
            toolbar,
            textvariable=self.detail_settings_text,
            command=self._open_job_settings,
            state="disabled",
        )
        self.detail_settings_button.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(4, 0))
        ttk.Button(toolbar, textvariable=self.pause_text, command=self._toggle_pause).grid(
            row=2, column=0, sticky="w", padx=(0, 4), pady=(6, 0)
        )
        ttk.Button(toolbar, text="⊗ Hủy", style="Danger.TButton", command=self._cancel_job).grid(
            row=2, column=1, padx=4, pady=(6, 0)
        )
        ttk.Button(toolbar, text="Xóa", command=self._delete_jobs).grid(
            row=2, column=2, padx=(4, 0), pady=(6, 0)
        )

        table = ttk.Frame(self.queue_card, style="Card.TFrame")
        table.grid(row=1, column=0, sticky="nsew")
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(0, weight=1)
        columns = ("check", "number", "title", "voice", "aspect", "status", "progress")
        self.job_table = ttk.Treeview(table, columns=columns, show="headings", selectmode="browse")
        headings = ("☐", "#", "Dự án", "Voice", "Khung hình", "Trạng thái", "Tiến trình")
        for column, heading in zip(columns, headings):
            self.job_table.heading(column, text=heading)
        self.job_table.column("check", width=38, minwidth=38, stretch=False, anchor="center")
        self.job_table.column("number", width=36, minwidth=36, stretch=False, anchor="center")
        self.job_table.column("title", width=150, minwidth=110, stretch=True)
        self.job_table.column("voice", width=95, minwidth=75, stretch=False)
        self.job_table.column("aspect", width=72, minwidth=65, stretch=False, anchor="center")
        self.job_table.column("status", width=82, minwidth=75, stretch=False)
        self.job_table.column("progress", width=115, minwidth=95, stretch=False)
        self.job_table.grid(row=0, column=0, sticky="nsew")
        self.job_table.tag_configure("running", foreground="#c66a00")
        self.job_table.tag_configure("completed", foreground="#15803d")
        self.job_table.tag_configure("failed", foreground="#c62828")
        self.job_table.bind("<<TreeviewSelect>>", self._job_selected)
        self.job_table.bind("<Button-1>", self._table_clicked, add="+")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.job_table.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll = ttk.Scrollbar(table, orient="horizontal", command=self.job_table.xview)
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        self.job_table.configure(
            yscrollcommand=scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

    def _build_script_card(self) -> None:
        self.script_card.grid_columnconfigure(0, weight=1)
        self.script_card.grid_rowconfigure(3, weight=1)
        ttk.Label(self.script_card, text="Kịch bản", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        ttk.Label(self.script_card, textvariable=self.detail_title, font=("Segoe UI", 11, "bold")).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(self.script_card, textvariable=self.detail_meta, style="Meta.TLabel").grid(
            row=2, column=0, sticky="w", pady=(2, 8)
        )
        script_frame = ttk.Frame(self.script_card, style="Card.TFrame")
        script_frame.grid(row=3, column=0, sticky="nsew")
        script_frame.grid_columnconfigure(0, weight=1)
        script_frame.grid_rowconfigure(0, weight=1)
        self.detail_script = tk.Text(
            script_frame, wrap="word", state="disabled", padx=10, pady=9, font=("Segoe UI", 10)
        )
        self.detail_script.grid(row=0, column=0, sticky="nsew")
        script_scroll = ttk.Scrollbar(script_frame, orient="vertical", command=self.detail_script.yview)
        script_scroll.grid(row=0, column=1, sticky="ns")
        self.detail_script.configure(yscrollcommand=script_scroll.set)

    def _build_detail_card(self) -> None:
        self.detail_card.grid_columnconfigure(0, weight=1)
        self.detail_card.grid_rowconfigure(1, weight=1)
        ttk.Label(self.detail_card, text="Xem trước", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.detail_canvas = tk.Canvas(
            self.detail_card, height=240, background="#111820", highlightthickness=0
        )
        self.detail_canvas.grid(row=1, column=0, sticky="nsew")
        self.detail_canvas.bind("<Configure>", self._render_detail_image)
        player_bar = ttk.Frame(self.detail_card, style="Card.TFrame")
        player_bar.grid(row=2, column=0, sticky="ew", pady=(5, 8))
        player_bar.grid_columnconfigure(1, weight=1)
        self.detail_play_button = ttk.Button(
            player_bar, text="▶", width=3, command=self._play_detail_video, state="disabled"
        )
        self.detail_play_button.grid(row=0, column=0, padx=(0, 5))
        ttk.Label(player_bar, textvariable=self.detail_video_time, style="Meta.TLabel").grid(
            row=0, column=1, sticky="e"
        )

        info = ttk.Frame(self.detail_card, style="Card.TFrame")
        info.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        info.grid_columnconfigure(0, weight=1)
        ttk.Label(info, textvariable=self.detail_phase, foreground="#c66a00").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Progressbar(info, maximum=100, variable=self.detail_progress).grid(
            row=1, column=0, sticky="ew", pady=(5, 0)
        )

    def _runner_event(self, kind: str, job_id: str, payload: object) -> None:
        self.events.put((kind, job_id, payload))

    def _add_projects(self) -> None:
        sources = filedialog.askopenfilenames(
            title="Thêm project.json hoặc ZIP vào hàng đợi",
            filetypes=[("Dự án video", "project.json *.zip"), ("Tất cả file", "*.*")],
        )
        if not sources:
            return
        profile = self.app._selected_voice_profile()
        voice_settings = VoiceSettings.load()
        added = 0
        errors: list[str] = []
        for source in sources:
            project = None
            try:
                project = load_project(source)
                needs_voice = bool(project.narration_cues or project.script_text) and not project.voice
                if needs_voice and (not profile or not voice_settings.cli_path.strip()):
                    raise ProjectError("Chưa chọn giọng hoặc chưa cấu hình OmniVoice.")
                job = self.store.add(
                    source_path=Path(source),
                    project=project,
                    aspect_ratio=self.app.aspect_ratio.get(),
                    pen_brand=self.app.pen_brand.get().strip() or project.pen_brand or "",
                    voice_profile_id=profile.profile_id if profile else "",
                    voice_name=profile.name if profile else "",
                    voice_audio_path=profile.audio_path if profile else None,
                    cli_path=voice_settings.cli_path.strip(),
                )
                self.checked_job_ids.add(job.job_id)
                added += 1
            except ProjectError as exc:
                errors.append(f"{Path(source).name}: {exc}")
            finally:
                if project:
                    project.close()
        self.refresh()
        if errors:
            messagebox.showwarning(
                "Một số dự án chưa được thêm", "\n".join(errors), parent=self.app
            )
        if added:
            self.worker_status.set(f"Đã thêm {added} job  •  Worker OmniVoice: sẵn sàng")

    def _set_filter(self, key: str) -> None:
        self.active_filter = key
        for name, button in self.kpi_buttons.items():
            button.configure(style="KPIActive.TButton" if name == key else "KPI.TButton")
        self.refresh()

    def _visible_jobs(self) -> list[VideoJob]:
        statuses = FILTERS[self.active_filter]
        return self.store.list(statuses)

    def _runnable_checked(self) -> list[str]:
        jobs = {job.job_id: job for job in self.store.list()}
        return [
            job_id for job_id in self.checked_job_ids
            if job_id in jobs and jobs[job_id].status in (WAITING, FAILED, CANCELED)
        ]

    def refresh(self) -> None:
        all_jobs = self.store.list()
        known = {job.job_id for job in all_jobs}
        self.checked_job_ids.intersection_update(known)
        counts = self.store.counts()
        self.total_kpi.set(f"TỔNG JOB\n{counts['total']}")
        self.running_kpi.set(f"ĐANG CHẠY\n{counts['running']}")
        self.waiting_kpi.set(f"ĐANG CHỜ\n{counts['waiting']}")
        self.completed_kpi.set(f"HOÀN TẤT\n{counts['completed']}")
        self.failed_kpi.set(f"LỖI\n{counts['failed']}")
        active_jobs = [job for job in all_jobs if job.status in (QUEUED, RUNNING)]
        if active_jobs:
            if self.batch_started_at is None:
                self.batch_started_at = time.monotonic()
            if self.batch_job_count <= 0:
                self.batch_job_count = len(active_jobs)
            self._update_run_button_clock()
            self.run_selected_button.configure(state="disabled")
        else:
            self.batch_started_at = None
            self.batch_job_count = 0
            runnable = self._runnable_checked()
            self.run_selected_text.set(run_button_label(len(runnable)))
            self.run_selected_button.configure(state="normal" if runnable else "disabled")
        setting_ids = settings_target_ids(all_jobs, self.checked_job_ids, self.detail_job_id)
        has_checked_settings = bool(self.checked_job_ids and setting_ids)
        self.detail_settings_text.set(
            settings_button_label(len(setting_ids), has_checked_settings)
        )
        self.detail_settings_button.configure(state="normal" if setting_ids else "disabled")

        selected_before = self.detail_job_id
        for row in self.job_table.get_children():
            self.job_table.delete(row)
        visible = self._visible_jobs()
        selectable_visible = [job.job_id for job in visible if job.status != RUNNING]
        self.job_table.heading(
            "check",
            text=header_checkbox_text(selectable_visible, self.checked_job_ids),
        )
        for job in visible:
            phase = job.phase or ("Chờ chọn" if job.status == WAITING else job_status_label(job.status))
            progress = f"{job.progress}% • {phase}" if job.progress else phase
            tag = (
                "running" if job.status == RUNNING else
                "completed" if job.status == COMPLETED else
                "failed" if job.status == FAILED else ""
            )
            self.job_table.insert(
                "",
                "end",
                iid=job.job_id,
                values=(
                    "☑" if job.job_id in self.checked_job_ids else "☐",
                    f"{job.position:02d}",
                    job.title,
                    job.voice_name or "Chưa chọn",
                    job.aspect_ratio,
                    job_status_label(job.status),
                    progress,
                ),
                tags=(tag,) if tag else (),
            )
        if selected_before and self.job_table.exists(selected_before):
            self.job_table.selection_set(selected_before)
            self.job_table.focus(selected_before)
        elif visible:
            first = visible[0].job_id
            self.job_table.selection_set(first)
            self.job_table.focus(first)
            self._show_job(first)
        else:
            self.detail_job_id = None
            self._clear_detail()

    def _table_clicked(self, event: tk.Event) -> None:
        region = self.job_table.identify_region(event.x, event.y)
        column = self.job_table.identify_column(event.x)
        row_id = self.job_table.identify_row(event.y)
        if region == "heading" and column == "#1":
            visible_ids = [job.job_id for job in self._visible_jobs() if job.status != RUNNING]
            if visible_ids and all(job_id in self.checked_job_ids for job_id in visible_ids):
                self.checked_job_ids.difference_update(visible_ids)
            else:
                self.checked_job_ids.update(visible_ids)
            self.after_idle(self.refresh)
        elif region == "cell" and row_id and column == "#1":
            if row_id in self.checked_job_ids:
                self.checked_job_ids.remove(row_id)
            else:
                self.checked_job_ids.add(row_id)
            self.after_idle(self.refresh)

    def _job_selected(self, _event: tk.Event | None = None) -> None:
        selected = self.job_table.selection()
        if selected:
            self._show_job(selected[0])

    def _run_selected(self) -> None:
        ids = self._runnable_checked()
        if ids:
            for job_id in ids:
                job = self.store.get(job_id)
                if job and job.status in (FAILED, CANCELED):
                    self.store.retry(job_id)
            queued = self.runner.queue(ids)
            if queued:
                self.batch_started_at = time.monotonic()
                self.batch_job_count = queued
            self.checked_job_ids.difference_update(ids)
            self.refresh()

    def _start_all(self) -> None:
        count = self.runner.queue_all()
        if not count:
            messagebox.showinfo("Hàng đợi", "Không có job mới đang chờ.", parent=self.app)
        else:
            self.batch_started_at = time.monotonic()
            self.batch_job_count = count
        self.refresh()

    def _update_run_button_clock(self) -> None:
        if self.batch_started_at is None or self.batch_job_count <= 0:
            return
        self.run_selected_text.set(
            running_button_label(
                self.batch_job_count,
                time.monotonic() - self.batch_started_at,
            )
        )

    def _toggle_pause(self) -> None:
        self.queue_paused = not self.queue_paused
        self.runner.set_paused(self.queue_paused)
        self.pause_text.set("▶ Tiếp tục" if self.queue_paused else "Ⅱ Tạm dừng")
        self.worker_status.set(
            "Hàng đợi đang tạm dừng; job hiện tại vẫn hoàn tất công đoạn."
            if self.queue_paused else "Worker OmniVoice: sẵn sàng  •  GPU: 1 tác vụ"
        )

    def _focused_job_id(self) -> str | None:
        selected = self.job_table.selection()
        return selected[0] if selected else self.detail_job_id

    def _cancel_job(self) -> None:
        job_id = self._focused_job_id()
        if not job_id:
            return
        job = self.store.get(job_id)
        if not job or job.status not in (RUNNING, QUEUED, WAITING):
            messagebox.showinfo("Không thể hủy", "Chỉ hủy được job đang chạy hoặc đang chờ.", parent=self.app)
            return
        if messagebox.askyesno("Hủy job", f"Hủy job “{job.title}”?", parent=self.app):
            self.runner.cancel(job_id)
            self.refresh()

    def _delete_jobs(self) -> None:
        ids = set(self.checked_job_ids)
        if not ids and self._focused_job_id():
            ids.add(self._focused_job_id() or "")
        ids.discard("")
        if not ids:
            return
        running = [job.title for job_id in ids if (job := self.store.get(job_id)) and job.status == RUNNING]
        if running:
            messagebox.showwarning("Không thể xóa", "Hãy hủy job đang chạy trước.", parent=self.app)
            return
        if messagebox.askyesno(
            "Xóa job", f"Xóa {len(ids)} job khỏi danh sách? File kết quả không bị xóa.", parent=self.app
        ):
            self.store.delete(ids)
            self.checked_job_ids.difference_update(ids)
            self.refresh()

    def _retry_job(self, job_id: str) -> None:
        if self.store.retry(job_id):
            self.runner.queue([job_id])
            self.refresh()

    def _open_result(self, job: VideoJob) -> None:
        if job.result_path and job.result_path.is_file():
            try:
                open_path(job.result_path)
            except OSError as exc:
                messagebox.showerror("Không thể mở video", str(exc), parent=self.app)

    def _open_selected_folder(self) -> None:
        job_id = self._focused_job_id()
        job = self.store.get(job_id) if job_id else None
        if not job:
            messagebox.showinfo("Chưa chọn job", "Hãy chọn một job trong hàng đợi.", parent=self.app)
            return
        job.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            open_path(job.output_dir)
        except OSError as exc:
            messagebox.showerror("Không thể mở thư mục", str(exc), parent=self.app)

    def _show_job(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if not job:
            return
        self.detail_job_id = job_id
        self.detail_aspect_ratio = job.aspect_ratio
        self.video_player.close()
        self.detail_play_button.configure(state="disabled", text="▶")
        self.detail_video_time.set("00:00 / 00:00")
        self.detail_title.set(job.title)
        self.detail_meta.set(
            f"{job.duration_seconds:.1f} giây  •  {job.aspect_ratio}  •  {job.voice_name or 'voice có sẵn'}"
        )
        self.detail_phase.set(
            f"{job_status_label(job.status)} — {job.phase or 'chưa chạy'}"
            + (f" — {job.error}" if job.status == FAILED and job.error else "")
        )
        self.detail_progress.set(job.progress)
        script = ""
        self._detail_image = None
        project = None
        try:
            project = load_project(job.source_path)
            script = project.script_text or " ".join(cue.text for cue in project.narration_cues)
            from PIL import Image
            if job.poster_path and job.poster_path.is_file():
                with Image.open(job.poster_path) as source:
                    self._detail_image = source.convert("RGB")
            elif project.scenes:
                with Image.open(project.scenes[0].image) as source:
                    self._detail_image = source.convert("RGB")
        except (ProjectError, OSError) as exc:
            script = f"Không thể đọc lại nguồn dự án: {exc}"
        finally:
            if project:
                project.close()
        self.detail_script.configure(state="normal")
        self.detail_script.delete("1.0", "end")
        self.detail_script.insert("1.0", script or "Dự án chưa có kịch bản.")
        self.detail_script.configure(state="disabled")
        if job.status == COMPLETED and job.result_path and job.result_path.is_file():
            self.detail_play_button.configure(state="normal")
        self._render_detail_image()
        self._show_job_logs(job_id)

    def _clear_detail(self) -> None:
        self.detail_title.set("Chưa chọn job")
        self.detail_meta.set("")
        self.detail_phase.set("Hàng đợi chưa có dự án")
        self.detail_progress.set(0)
        self.detail_aspect_ratio = "16:9"
        self._detail_image = None
        self.detail_canvas.delete("all")
        self.detail_canvas.create_text(250, 100, text="Thêm dự án để bắt đầu", fill="#9ca3af")
        self.detail_script.configure(state="normal")
        self.detail_script.delete("1.0", "end")
        self.detail_script.configure(state="disabled")
        self._show_job_logs("")

    def _render_detail_image(self, _event: tk.Event | None = None) -> None:
        if not hasattr(self, "detail_canvas"):
            return
        width = max(1, self.detail_canvas.winfo_width())
        height = max(1, self.detail_canvas.winfo_height())
        self.detail_canvas.delete("all")
        if self._detail_image is None:
            self.detail_canvas.create_text(width // 2, height // 2, text="Chưa có preview", fill="#9ca3af")
            return
        try:
            from PIL import ImageOps, ImageTk
            target_size = preview_frame_size(
                max(1, width - 16),
                max(1, height - 16),
                self.detail_aspect_ratio,
            )
            preview = ImageOps.fit(self._detail_image, target_size)
            self._detail_photo = ImageTk.PhotoImage(preview)
            self.detail_canvas.create_image(width // 2, height // 2, image=self._detail_photo, anchor="center")
            target_width, target_height = target_size
            left = (width - target_width) // 2
            top = (height - target_height) // 2
            self.detail_canvas.create_rectangle(
                left,
                top,
                left + target_width,
                top + target_height,
                outline="#22c55e",
                width=2,
            )
            self.detail_canvas.create_text(
                left + 8,
                top + 8,
                text=self.detail_aspect_ratio,
                fill="#ffffff",
                anchor="nw",
                font=("Segoe UI", 9, "bold"),
            )
        except Exception:
            self.detail_canvas.create_text(width // 2, height // 2, text="Không thể hiển thị preview", fill="#9ca3af")

    def _open_job_settings(self) -> None:
        all_jobs = self.store.list()
        target_ids = settings_target_ids(all_jobs, self.checked_job_ids, self.detail_job_id)
        target_jobs = [job for job in all_jobs if job.job_id in target_ids]
        if not target_jobs:
            messagebox.showinfo("Chưa chọn job", "Hãy chọn một job để xem thiết lập.", parent=self.app)
            return
        focused_job = self.store.get(self.detail_job_id or "")
        editable_jobs = [target for target in target_jobs if job_settings_editable(target.status)]
        locked_jobs = [target for target in target_jobs if not job_settings_editable(target.status)]
        if editable_jobs:
            job = (
                focused_job
                if focused_job and focused_job.job_id in {target.job_id for target in editable_jobs}
                else editable_jobs[0]
            )
        else:
            job = focused_job if focused_job and focused_job.job_id in target_ids else target_jobs[0]
        bulk_edit = len(target_jobs) > 1
        if self.settings_dialog and self.settings_dialog.winfo_exists():
            self.settings_dialog.destroy()

        dialog = tk.Toplevel(self.app)
        self.settings_dialog = dialog
        dialog.title(
            f"Thiết lập video — {len(target_jobs)} job đã chọn"
            if bulk_edit
            else f"Thiết lập video — {job.title}"
        )
        dialog.transient(self.app)
        dialog.resizable(True, False)
        dialog.minsize(620, 420)
        dialog.grid_columnconfigure(0, weight=1)

        editable = bool(editable_jobs)
        aspect_ratio = tk.StringVar(value=job.aspect_ratio)
        pen_brand = tk.StringVar(value=job.pen_brand)
        output_dir = tk.StringVar(value=str(job.output_dir.parent if bulk_edit else job.output_dir))
        voice_library = VoiceLibrary.load()
        library_profiles = [
            profile for profile in voice_library.profiles if profile.audio_path.is_file()
        ]
        voice_options: list[tuple[str, str, Path]] = []
        seen_voice_ids: set[str] = set()
        canonical_voice_ids: dict[str, str] = {}
        for target in target_jobs:
            if target.voice_audio_path and target.voice_audio_path.is_file():
                matched_profile = matching_voice_profile(
                    library_profiles,
                    target.voice_profile_id,
                    target.voice_name,
                    target.voice_audio_path,
                )
                current_voice_id = (
                    matched_profile.profile_id
                    if matched_profile
                    else target.voice_profile_id or f"job:{target.job_id}"
                )
                current_voice_name = (
                    matched_profile.name if matched_profile else target.voice_name or "Giọng hiện tại"
                )
                current_voice_path = (
                    matched_profile.audio_path if matched_profile else target.voice_audio_path
                )
                canonical_voice_ids[target.job_id] = current_voice_id
                if current_voice_id not in seen_voice_ids:
                    voice_options.append(
                        (current_voice_id, current_voice_name, current_voice_path)
                    )
                    seen_voice_ids.add(current_voice_id)
        for profile in library_profiles:
            if profile.profile_id not in seen_voice_ids:
                voice_options.append((profile.profile_id, profile.name, profile.audio_path))
                seen_voice_ids.add(profile.profile_id)
        voice_values = [name for _profile_id, name, _audio_path in voice_options]
        saved_voice_settings = VoiceSettings.load()
        voice_name = tk.StringVar(value=job.voice_name or (voice_values[0] if voice_values else ""))

        card = ttk.Frame(dialog, padding=18)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)
        ttk.Label(card, text="Thiết lập video", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            card,
            text=(
                (
                    f"Áp dụng đồng loạt cho {len(editable_jobs)} job; "
                    "mỗi job vẫn có thư mục kết quả riêng."
                    + (f" Bỏ qua {len(locked_jobs)} job đang chạy/đã xếp hàng." if locked_jobs else "")
                    if bulk_edit and editable
                    else (
                        "Lưu job đã xong/lỗi sẽ đưa job về Đang chờ để chạy lại."
                        if editable and job.status != WAITING
                        else "Thay đổi được lưu riêng cho job này."
                    )
                )
                if editable
                else "Các job đã chọn đang chạy hoặc đã xếp hàng nên cấu hình được khóa."
            ),
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 10))

        preview_card = ttk.Frame(card)
        preview_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        preview_card.grid_columnconfigure(0, weight=1)
        settings_preview_label = tk.StringVar(value=f"Xem trước khung hình {aspect_ratio.get()}")
        ttk.Label(preview_card, textvariable=settings_preview_label, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        settings_preview = tk.Canvas(
            preview_card,
            height=170,
            background="#111820",
            highlightthickness=0,
        )
        settings_preview.grid(row=1, column=0, sticky="ew")
        settings_preview_photo = None

        def render_settings_preview(_event: tk.Event | None = None) -> None:
            nonlocal settings_preview_photo
            settings_preview_label.set(f"Xem trước khung hình {aspect_ratio.get()} • crop giữa")
            width = max(1, settings_preview.winfo_width())
            height = max(1, settings_preview.winfo_height())
            settings_preview.delete("all")
            if self._detail_image is None:
                settings_preview.create_text(
                    width // 2,
                    height // 2,
                    text="Chưa có ảnh để xem trước",
                    fill="#9ca3af",
                )
                return
            try:
                from PIL import ImageOps, ImageTk

                target_size = preview_frame_size(width - 16, height - 16, aspect_ratio.get())
                preview = ImageOps.fit(self._detail_image, target_size)
                settings_preview_photo = ImageTk.PhotoImage(preview)
                settings_preview.create_image(
                    width // 2,
                    height // 2,
                    image=settings_preview_photo,
                    anchor="center",
                )
                target_width, target_height = target_size
                left = (width - target_width) // 2
                top = (height - target_height) // 2
                settings_preview.create_rectangle(
                    left,
                    top,
                    left + target_width,
                    top + target_height,
                    outline="#22c55e",
                    width=2,
                )
            except Exception:
                settings_preview.create_text(
                    width // 2,
                    height // 2,
                    text="Không thể hiển thị preview",
                    fill="#9ca3af",
                )

        settings_preview.bind("<Configure>", render_settings_preview)

        ttk.Label(card, text="Giọng đọc", font=("Segoe UI", 9, "bold")).grid(
            row=3, column=0, sticky="w", padx=(0, 14), pady=7
        )
        voice_row = ttk.Frame(card)
        voice_row.grid(row=3, column=1, sticky="ew", pady=7)
        voice_row.grid_columnconfigure(0, weight=1)
        voice_combo = ttk.Combobox(
            voice_row,
            textvariable=voice_name,
            values=voice_values,
            state="readonly" if editable and voice_values else "disabled",
        )
        voice_combo.grid(row=0, column=0, sticky="ew", padx=(0, 7))
        if voice_values:
            selected_index = preferred_voice_index(
                voice_options,
                canonical_voice_ids.get(job.job_id, job.voice_profile_id),
                job.voice_name,
                saved_voice_settings.selected_profile_id,
            )
            voice_combo.current(selected_index)
            voice_combo.set(voice_values[selected_index])
            voice_name.set(voice_values[selected_index])

        def selected_voice() -> tuple[str, str, Path] | None:
            index = voice_combo.current()
            return voice_options[index] if 0 <= index < len(voice_options) else None

        library_profile_ids = {profile.profile_id for profile in voice_library.profiles}

        def remember_default_voice(_event: tk.Event | None = None) -> None:
            option = selected_voice()
            if option and option[0] in library_profile_ids:
                current = VoiceSettings.load()
                VoiceSettings(
                    cli_path=current.cli_path,
                    selected_profile_id=option[0],
                ).save()

        voice_combo.bind("<<ComboboxSelected>>", remember_default_voice)

        def preview_voice() -> None:
            option = selected_voice()
            if not option:
                messagebox.showinfo("Chưa có giọng", "Hãy thêm giọng trong phần Cài đặt giọng.", parent=dialog)
                return
            try:
                play_audio(option[2])
            except OmniVoiceError as exc:
                messagebox.showerror("Không thể nghe thử", str(exc), parent=dialog)

        ttk.Button(voice_row, text="▶ Nghe thử", command=preview_voice).grid(row=0, column=1)

        ttk.Label(card, text="Khung hình", font=("Segoe UI", 9, "bold")).grid(
            row=4, column=0, sticky="w", padx=(0, 14), pady=7
        )
        ratio_row = ttk.Frame(card)
        ratio_row.grid(row=4, column=1, sticky="w", pady=7)
        for column, ratio in enumerate(ASPECT_RATIOS):
            ttk.Radiobutton(
                ratio_row,
                text=ratio,
                value=ratio,
                variable=aspect_ratio,
                state="normal" if editable else "disabled",
                command=render_settings_preview,
            ).grid(row=0, column=column, padx=(0, 18))

        ttk.Label(card, text="Chữ trên bút", font=("Segoe UI", 9, "bold")).grid(
            row=5, column=0, sticky="w", padx=(0, 14), pady=7
        )
        ttk.Entry(
            card,
            textvariable=pen_brand,
            state="normal" if editable else "disabled",
        ).grid(row=5, column=1, sticky="ew", pady=7)

        ttk.Label(
            card,
            text="Thư mục gốc" if bulk_edit else "Nơi lưu",
            font=("Segoe UI", 9, "bold"),
        ).grid(
            row=6, column=0, sticky="w", padx=(0, 14), pady=7
        )
        output_row = ttk.Frame(card)
        output_row.grid(row=6, column=1, sticky="ew", pady=7)
        output_row.grid_columnconfigure(0, weight=1)
        ttk.Entry(
            output_row,
            textvariable=output_dir,
            state="normal" if editable else "disabled",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 7))

        def choose_output() -> None:
            selected = filedialog.askdirectory(
                parent=dialog,
                title="Chọn thư mục gốc cho các job" if bulk_edit else "Chọn thư mục lưu riêng cho job",
                initialdir=output_dir.get(),
            )
            if selected:
                output_dir.set(str(Path(selected).resolve()))

        ttk.Button(
            output_row,
            text="Chọn…",
            command=choose_output,
            state="normal" if editable else "disabled",
        ).grid(row=0, column=1)

        ttk.Separator(card).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 10))

        def save_settings() -> None:
            brand = pen_brand.get().strip()
            if len(brand) > 40:
                messagebox.showwarning("Chữ trên bút quá dài", "Chỉ nhập tối đa 40 ký tự.", parent=dialog)
                return
            raw_output = output_dir.get().strip()
            if not raw_output:
                messagebox.showwarning("Thiếu nơi lưu", "Hãy chọn thư mục lưu kết quả.", parent=dialog)
                return
            option = selected_voice()
            if any(target.voice_audio_path for target in editable_jobs) and option is None:
                messagebox.showwarning("Thiếu giọng đọc", "Hãy chọn một giọng đọc hợp lệ.", parent=dialog)
                return
            settings = VoiceSettings.load()
            changed_ids: list[str] = []
            try:
                output_root = Path(raw_output)
                for target in editable_jobs:
                    changed = self.store.update_settings(
                        target.job_id,
                        aspect_ratio=aspect_ratio.get(),
                        pen_brand=brand,
                        voice_profile_id=option[0] if option else "",
                        voice_name=option[1] if option else "",
                        voice_audio_path=option[2] if option else None,
                        cli_path=settings.cli_path.strip() or target.cli_path,
                        output_dir=(
                            bulk_output_directory(output_root, target.job_id)
                            if bulk_edit
                            else output_root
                        ),
                    )
                    if changed:
                        changed_ids.append(target.job_id)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Không thể lưu thiết lập", str(exc), parent=dialog)
                return
            if not changed_ids:
                messagebox.showwarning(
                    "Job đã bị khóa",
                    "Worker đã lấy các job này. Hãy hủy job trước khi thay đổi cấu hình.",
                    parent=dialog,
                )
                return
            if option and option[0] in library_profile_ids:
                VoiceSettings(
                    cli_path=settings.cli_path.strip() or job.cli_path,
                    selected_profile_id=option[0],
                ).save()
            VideoPreferences(aspect_ratio=aspect_ratio.get(), pen_brand=brand).save()
            self.app.aspect_ratio.set(aspect_ratio.get())
            self.app.pen_brand.set(brand)
            self.app._refresh_voice_profiles()
            stop_audio()
            dialog.destroy()
            self.checked_job_ids.update(changed_ids)
            self.refresh()
            if self.detail_job_id:
                self._show_job(self.detail_job_id)
            skipped = len(target_jobs) - len(changed_ids)
            self.worker_status.set(
                f"Đã áp dụng thiết lập cho {len(changed_ids)} job"
                + (f"  •  Bỏ qua {skipped} job đang bị khóa" if skipped else "")
            )

        actions = ttk.Frame(card)
        actions.grid(row=8, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text="Hủy", command=dialog.destroy).pack(side="left", padx=(0, 7))
        if editable:
            ttk.Button(
                actions,
                text=f"Áp dụng cho {len(editable_jobs)} job" if bulk_edit else "Lưu thay đổi",
                style="Accent.TButton",
                command=save_settings,
            ).pack(
                side="left"
            )
        else:
            ttk.Button(actions, text="Đóng", command=dialog.destroy).pack(side="left")

        dialog.update_idletasks()
        width = max(700, dialog.winfo_reqwidth())
        height = max(610, dialog.winfo_reqheight())
        x = self.app.winfo_rootx() + max(0, (self.app.winfo_width() - width) // 2)
        y = self.app.winfo_rooty() + max(0, (self.app.winfo_height() - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        def close_dialog() -> None:
            stop_audio()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.grab_set()
        dialog.focus_set()
        dialog.after_idle(render_settings_preview)

    def _show_job_logs(self, job_id: str) -> None:
        self.job_log.configure(state="normal")
        self.job_log.delete("1.0", "end")
        if job_id:
            for created_at, message in self.store.logs(job_id):
                time_text = created_at.split("T")[-1].split("+")[0]
                self.job_log.insert("end", f"[{time_text}] {message}\n")
        self.job_log.configure(state="disabled")

    def _play_detail_video(self) -> None:
        job = self.store.get(self.detail_job_id or "")
        if not job or not job.result_path or not job.result_path.is_file():
            return
        try:
            if self.video_player.path != job.result_path:
                self.video_player.load(job.result_path, job.preview_audio_path)
            self.video_player.play_pause()
        except VideoPlaybackError as exc:
            messagebox.showerror("Không thể phát video", str(exc), parent=self.app)

    def _video_position(self, position: float, duration: float) -> None:
        self.detail_video_time.set(f"{format_media_time(position)} / {format_media_time(duration)}")

    def _video_state(self, state: str) -> None:
        self.detail_play_button.configure(text="Ⅱ" if state == "playing" else "▶")

    def _video_error(self, message: str) -> None:
        self.worker_status.set(f"Lỗi trình phát: {message}")

    def _apply_workspace_layout(self, mode: str) -> None:
        if mode == self._workspace_layout:
            return
        self._workspace_layout = mode
        for card in (self.queue_card, self.script_card, self.detail_card):
            card.grid_forget()
        for column in range(3):
            self.workspace.grid_columnconfigure(column, weight=0, minsize=0)
        for row in range(3):
            self.workspace.grid_rowconfigure(row, weight=0, minsize=0)

        if mode == "three":
            self.workspace.grid_rowconfigure(0, weight=1)
            self.workspace.grid_columnconfigure(0, weight=9, minsize=340)
            self.workspace.grid_columnconfigure(1, weight=10, minsize=340)
            self.workspace.grid_columnconfigure(2, weight=10, minsize=340)
            self.queue_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
            self.script_card.grid(row=0, column=1, sticky="nsew", padx=5)
            self.detail_card.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        elif mode == "two":
            self.workspace.grid_columnconfigure(0, weight=4, minsize=330)
            self.workspace.grid_columnconfigure(1, weight=6, minsize=390)
            self.workspace.grid_rowconfigure(0, weight=1)
            self.workspace.grid_rowconfigure(1, weight=1)
            self.queue_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 6))
            self.script_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 5))
            self.detail_card.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(5, 0))
        else:
            self.workspace.grid_columnconfigure(0, weight=1)
            self.workspace.grid_rowconfigure(0, weight=2)
            self.workspace.grid_rowconfigure(1, weight=1)
            self.workspace.grid_rowconfigure(2, weight=2)
            self.queue_card.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
            self.script_card.grid(row=1, column=0, sticky="nsew", pady=5)
            self.detail_card.grid(row=2, column=0, sticky="nsew", pady=(5, 0))

    def _poll_events(self) -> None:
        if self._closed:
            return
        table_dirty = False
        detail_dirty = False
        log_dirty = False
        try:
            while True:
                kind, job_id, payload = self.events.get_nowait()
                if kind == "progress" and self.detail_job_id == job_id:
                    phase, value = payload
                    self.detail_phase.set(str(phase))
                    self.detail_progress.set(int(value))
                    table_dirty = True
                elif kind == "progress":
                    table_dirty = True
                elif kind == "log" and self.detail_job_id == job_id:
                    log_dirty = True
                elif kind == "failed":
                    self.worker_status.set("Một job bị lỗi; hàng đợi vẫn tiếp tục.")
                    table_dirty = True
                    detail_dirty = self.detail_job_id == job_id
                elif kind == "completed":
                    self.worker_status.set("Đã hoàn tất một job; đang kiểm tra hàng đợi tiếp theo.")
                    table_dirty = True
                    detail_dirty = self.detail_job_id == job_id
                elif kind in ("changed", "queue", "idle", "paused"):
                    table_dirty = True
                    detail_dirty = detail_dirty or self.detail_job_id == job_id
        except queue.Empty:
            pass
        if table_dirty:
            self.refresh()
        else:
            self._update_run_button_clock()
        if detail_dirty and self.detail_job_id:
            self._show_job(self.detail_job_id)
        elif log_dirty and self.detail_job_id:
            self._show_job_logs(self.detail_job_id)
        self.after(150, self._poll_events)

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        self._apply_workspace_layout(multi_job_layout(event.width))

    def close(self) -> None:
        self._closed = True
        if self.settings_dialog and self.settings_dialog.winfo_exists():
            self.settings_dialog.destroy()
        self.runner.stop()
        self.video_player.close()
