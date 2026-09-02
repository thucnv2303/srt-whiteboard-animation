from __future__ import annotations

import os
import queue
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from .jobs import (
    CANCELED,
    COMPLETED,
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
from .video_player import TkVideoPlayer, VideoPlaybackError, format_media_time
from .voice import VoiceSettings

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
        self.settings_expanded = False
        self.queue_paused = False
        self._detail_image = None
        self._detail_photo = None
        self._closed = False

        self.total_kpi = tk.StringVar(value="TỔNG JOB\n0")
        self.running_kpi = tk.StringVar(value="ĐANG CHẠY\n0")
        self.waiting_kpi = tk.StringVar(value="ĐANG CHỜ\n0")
        self.completed_kpi = tk.StringVar(value="HOÀN TẤT\n0")
        self.failed_kpi = tk.StringVar(value="LỖI\n0")
        self.run_selected_text = tk.StringVar(value=run_button_label(0))
        self.pause_text = tk.StringVar(value="Ⅱ Tạm dừng hàng đợi")
        self.detail_title = tk.StringVar(value="Chưa chọn job")
        self.detail_meta = tk.StringVar(value="")
        self.detail_phase = tk.StringVar(value="Chọn một job trong hàng đợi")
        self.detail_progress = tk.IntVar(value=0)
        self.detail_settings_heading = tk.StringVar(value="Thiết lập video  ▸")
        self.detail_video_time = tk.StringVar(value="00:00 / 00:00")
        self.worker_status = tk.StringVar(value="Worker OmniVoice: sẵn sàng  •  GPU: 1 tác vụ")

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
        self.workspace.grid_columnconfigure(0, weight=3)
        self.workspace.grid_columnconfigure(1, weight=2)
        self.queue_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=12)
        self.detail_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=12)
        self._build_queue_card()
        self._build_detail_card()
        self.queue_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.detail_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

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
        ttk.Label(toolbar, text="Hàng đợi xử lý", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.run_selected_button = ttk.Button(
            toolbar, textvariable=self.run_selected_text, command=self._run_selected
        )
        self.run_selected_button.grid(row=0, column=1, padx=(6, 4))
        ttk.Button(toolbar, textvariable=self.pause_text, command=self._toggle_pause).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(toolbar, text="⊗ Hủy job", style="Danger.TButton", command=self._cancel_job).grid(
            row=0, column=3, padx=4
        )
        ttk.Button(toolbar, text="Xóa job", command=self._delete_jobs).grid(row=0, column=4, padx=(4, 0))

        table = ttk.Frame(self.queue_card, style="Card.TFrame")
        table.grid(row=1, column=0, sticky="nsew")
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(0, weight=1)
        columns = ("check", "number", "title", "status", "progress", "duration", "result")
        self.job_table = ttk.Treeview(table, columns=columns, show="headings", selectmode="browse")
        headings = ("☐", "#", "Dự án", "Trạng thái", "Tiến trình", "Thời lượng", "Kết quả")
        for column, heading in zip(columns, headings):
            self.job_table.heading(column, text=heading)
        self.job_table.column("check", width=38, minwidth=38, stretch=False, anchor="center")
        self.job_table.column("number", width=42, minwidth=42, stretch=False, anchor="center")
        self.job_table.column("title", width=230, minwidth=150, stretch=True)
        self.job_table.column("status", width=95, minwidth=85, stretch=False)
        self.job_table.column("progress", width=130, minwidth=105, stretch=False)
        self.job_table.column("duration", width=80, minwidth=70, stretch=False, anchor="center")
        self.job_table.column("result", width=82, minwidth=72, stretch=False, anchor="center")
        self.job_table.grid(row=0, column=0, sticky="nsew")
        self.job_table.tag_configure("running", foreground="#c66a00")
        self.job_table.tag_configure("completed", foreground="#15803d")
        self.job_table.tag_configure("failed", foreground="#c62828")
        self.job_table.bind("<<TreeviewSelect>>", self._job_selected)
        self.job_table.bind("<Button-1>", self._table_clicked, add="+")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.job_table.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.job_table.configure(yscrollcommand=scroll.set)

    def _build_detail_card(self) -> None:
        self.detail_card.grid_columnconfigure(0, weight=1)
        self.detail_card.grid_rowconfigure(4, weight=1)
        ttk.Label(self.detail_card, text="Chi tiết job", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.detail_canvas = tk.Canvas(
            self.detail_card, height=190, background="#111820", highlightthickness=0
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
        ttk.Label(info, textvariable=self.detail_title, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(info, textvariable=self.detail_meta, style="Meta.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 6)
        )
        ttk.Label(info, textvariable=self.detail_phase, foreground="#c66a00").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Progressbar(info, maximum=100, variable=self.detail_progress).grid(
            row=3, column=0, sticky="ew", pady=(5, 0)
        )

        script_frame = ttk.LabelFrame(self.detail_card, text="Kịch bản", padding=8)
        script_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        script_frame.grid_columnconfigure(0, weight=1)
        script_frame.grid_rowconfigure(0, weight=1)
        self.detail_script = tk.Text(
            script_frame, height=7, wrap="word", state="disabled", padx=8, pady=7, font=("Segoe UI", 10)
        )
        self.detail_script.grid(row=0, column=0, sticky="nsew")
        script_scroll = ttk.Scrollbar(script_frame, orient="vertical", command=self.detail_script.yview)
        script_scroll.grid(row=0, column=1, sticky="ns")
        self.detail_script.configure(yscrollcommand=script_scroll.set)

        self.detail_settings_button = ttk.Button(
            self.detail_card,
            textvariable=self.detail_settings_heading,
            style="Section.TButton",
            command=self._toggle_detail_settings,
        )
        self.detail_settings_button.grid(row=5, column=0, sticky="ew")
        self.detail_settings_body = ttk.Frame(self.detail_card, padding=(9, 8))
        self.detail_settings_text = ttk.Label(
            self.detail_settings_body, text="", style="Subtitle.TLabel", justify="left"
        )
        self.detail_settings_text.grid(row=0, column=0, sticky="w")

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
            if job_id in jobs and jobs[job_id].status == WAITING
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
        runnable = self._runnable_checked()
        self.run_selected_text.set(run_button_label(len(runnable)))
        self.run_selected_button.configure(state="normal" if runnable else "disabled")

        selected_before = self.detail_job_id
        for row in self.job_table.get_children():
            self.job_table.delete(row)
        visible = self._visible_jobs()
        for job in visible:
            action = "Mở video" if job.status == COMPLETED else "Chạy lại" if job.status == FAILED else "—"
            duration = f"{job.duration_seconds:.1f} giây" if job.duration_seconds else "—"
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
                    job_status_label(job.status),
                    progress,
                    duration,
                    action,
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
            visible_waiting = [job.job_id for job in self._visible_jobs() if job.status == WAITING]
            if visible_waiting and all(job_id in self.checked_job_ids for job_id in visible_waiting):
                self.checked_job_ids.difference_update(visible_waiting)
            else:
                self.checked_job_ids.update(visible_waiting)
            self.after_idle(self.refresh)
        elif region == "cell" and row_id and column == "#1":
            if row_id in self.checked_job_ids:
                self.checked_job_ids.remove(row_id)
            else:
                self.checked_job_ids.add(row_id)
            self.after_idle(self.refresh)
        elif region == "cell" and row_id and column == "#7":
            job = self.store.get(row_id)
            if job and job.status == FAILED:
                self.after_idle(lambda: self._retry_job(row_id))
            elif job and job.status == COMPLETED and job.result_path:
                self.after_idle(lambda: self._open_result(job))

    def _job_selected(self, _event: tk.Event | None = None) -> None:
        selected = self.job_table.selection()
        if selected:
            self._show_job(selected[0])

    def _run_selected(self) -> None:
        ids = self._runnable_checked()
        if ids:
            self.runner.queue(ids)
            self.checked_job_ids.difference_update(ids)
            self.refresh()

    def _start_all(self) -> None:
        count = self.runner.queue_all()
        if not count:
            messagebox.showinfo("Hàng đợi", "Không có job mới đang chờ.", parent=self.app)
        self.refresh()

    def _toggle_pause(self) -> None:
        self.queue_paused = not self.queue_paused
        self.runner.set_paused(self.queue_paused)
        self.pause_text.set("▶ Tiếp tục hàng đợi" if self.queue_paused else "Ⅱ Tạm dừng hàng đợi")
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
        self.detail_settings_text.configure(
            text=(
                f"Giọng đọc: {job.voice_name or 'Voice trong dự án'}\n"
                f"Khung hình: {job.aspect_ratio}\n"
                f"Chữ trên bút: {job.pen_brand or 'Không có'}\n"
                f"Nơi lưu: {job.output_dir}"
            )
        )
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
            preview = ImageOps.contain(self._detail_image, (max(1, width - 16), max(1, height - 16)))
            self._detail_photo = ImageTk.PhotoImage(preview)
            self.detail_canvas.create_image(width // 2, height // 2, image=self._detail_photo, anchor="center")
        except Exception:
            self.detail_canvas.create_text(width // 2, height // 2, text="Không thể hiển thị preview", fill="#9ca3af")

    def _toggle_detail_settings(self) -> None:
        self.settings_expanded = not self.settings_expanded
        self.detail_settings_heading.set("Thiết lập video  ▾" if self.settings_expanded else "Thiết lập video  ▸")
        if self.settings_expanded:
            self.detail_settings_body.grid(row=6, column=0, sticky="ew")
        else:
            self.detail_settings_body.grid_remove()

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
        if detail_dirty and self.detail_job_id:
            self._show_job(self.detail_job_id)
        elif log_dirty and self.detail_job_id:
            self._show_job_logs(self.detail_job_id)
        self.after(150, self._poll_events)

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        self.queue_card.grid_forget()
        self.detail_card.grid_forget()
        if event.width >= 1000:
            self.workspace.grid_columnconfigure(0, weight=3)
            self.workspace.grid_columnconfigure(1, weight=2)
            self.workspace.grid_rowconfigure(0, weight=1)
            self.workspace.grid_rowconfigure(1, weight=0)
            self.queue_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
            self.detail_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        else:
            self.workspace.grid_columnconfigure(0, weight=1)
            self.workspace.grid_columnconfigure(1, weight=0)
            self.workspace.grid_rowconfigure(0, weight=1)
            self.workspace.grid_rowconfigure(1, weight=1)
            self.queue_card.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
            self.detail_card.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def close(self) -> None:
        self._closed = True
        self.runner.stop()
        self.video_player.close()
