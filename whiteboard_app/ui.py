from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .project import ProjectError, Scene, VideoProject, load_project
from .renderer import (
    ASPECT_RATIOS,
    RenderError,
    create_video_poster,
    create_video_preview_audio,
    run_pipeline,
)
from .timeline import TimelineError, TimelineResult, compile_timeline
from .video_player import TkVideoPlayer, VideoPlaybackError, format_media_time
from .multi_job_ui import MultiJobView
from .voice import (
    OmniVoiceError,
    VoiceLibrary,
    VoiceProfile,
    VoiceSettings,
    generate_clone_voice,
    generate_cue_voices,
    play_audio,
    stop_audio,
)
from .voice_dialog import VoiceManagerDialog


def responsive_layout(width: int) -> str:
    """Chọn bố cục mà không cần khởi tạo Tk trong unit test."""
    return "horizontal" if width >= 920 else "stacked"


def video_settings_heading(expanded: bool) -> str:
    return "Thiết lập video  ▾" if expanded else "Thiết lập video  ▸"


@dataclass(frozen=True)
class PreviewItem:
    item_id: str
    title: str
    scene: Scene
    region: tuple[int, int, int, int] | None = None


def project_preview_items(project: VideoProject) -> list[PreviewItem]:
    """Biến narration cue thành các phân cảnh nội dung để UI hiển thị đầy đủ."""
    annotations: dict[str, dict[str, object]] = {}
    scenes = {scene.scene_id: scene for scene in project.scenes}
    for scene in project.scenes:
        try:
            data = json.loads(scene.annotation.read_text(encoding="utf-8-sig"))
            annotations[scene.scene_id] = data if isinstance(data, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            annotations[scene.scene_id] = {}

    items: list[PreviewItem] = []
    for cue in project.narration_cues:
        scene = scenes[cue.scene_id]
        raw_elements = annotations[cue.scene_id].get("elements", [])
        element_lookup = {
            str(element.get("id")): element
            for element in raw_elements
            if isinstance(element, dict) and isinstance(element.get("id"), str)
        }
        labels: list[str] = []
        regions: list[tuple[int, int, int, int]] = []
        for element_id in cue.element_ids:
            element = element_lookup.get(element_id, {})
            label = element.get("label")
            if isinstance(label, str) and label.strip():
                labels.append(label.strip())
            region = element.get("region")
            if isinstance(region, dict):
                values = (region.get("x"), region.get("y"), region.get("width"), region.get("height"))
                if all(isinstance(value, int) for value in values):
                    x, y, width, height = values
                    if width > 0 and height > 0:
                        regions.append((x, y, x + width, y + height))
        union_region = None
        if regions:
            union_region = (
                min(region[0] for region in regions),
                min(region[1] for region in regions),
                max(region[2] for region in regions),
                max(region[3] for region in regions),
            )
        fallback = cue.text.split(".", 1)[0].strip()
        title = " + ".join(labels) or fallback or cue.cue_id
        items.append(PreviewItem(cue.cue_id, title, scene, union_region))
    if items:
        return items
    return [PreviewItem(scene.scene_id, scene.title, scene) for scene in project.scenes]


def open_media(path: Path) -> None:
    """Mở video bằng trình phát mặc định của hệ điều hành."""
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class WhiteboardApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Studio video vẽ tay")
        self.geometry("1280x820")
        self.minsize(760, 640)
        self.project: VideoProject | None = None
        self.output_dir: Path | None = None
        self.cancel_event = threading.Event()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.voice_settings = VoiceSettings.load()
        self.voice_library = VoiceLibrary.load()
        self._voice_profile_options: list[VoiceProfile] = []
        self._layout_mode = ""
        self._preview_image = None
        self._preview_photo = None
        self._preview_after: str | None = None
        self._preview_items: dict[str, PreviewItem] = {}
        self._active_preview_item: PreviewItem | None = None
        self._preview_kind = "scene"
        self._final_video: Path | None = None
        self._final_poster: Path | None = None
        self._final_preview_audio: Path | None = None
        self._seeking_video = False
        self.video_player: TkVideoPlayer | None = None

        self.aspect_ratio = tk.StringVar(value="16:9")
        self.pen_brand = tk.StringVar(value="Ăn dặm mẹ Dâu")
        self.project_title_text = tk.StringVar(value="Chưa có dự án")
        self.project_meta_text = tk.StringVar(value="0 cảnh  •  chưa có thời lượng")
        self.project_source_text = tk.StringVar(value="GPT sẽ gửi ảnh và kịch bản vào gói dự án")
        self.voice_path = tk.StringVar(value="Chưa tạo âm thanh")
        self.timeline_text = tk.StringVar(value="Timeline: chưa đồng bộ")
        self.selected_voice_text = tk.StringVar(value="Chưa có giọng đã lưu")
        self.output_path = tk.StringVar(value="Tự động: thư mục output của dự án")
        self.result_path = tk.StringVar(value="Chưa có video kết quả")
        self.video_seek = tk.DoubleVar(value=0.0)
        self.video_time = tk.StringVar(value="00:00 / 00:00")
        self.progress_text = tk.StringVar(value="Sẵn sàng")
        self.video_settings_expanded = False
        self.video_settings_heading = tk.StringVar(value=video_settings_heading(False))

        self._build_styles()
        self._build_ui()
        self.video_player = TkVideoPlayer(
            self,
            self.preview_canvas,
            on_position=self._video_position_changed,
            on_state=self._video_state_changed,
            on_error=self._video_error,
        )
        self._refresh_voice_profiles()
        self.bind("<Configure>", self._on_window_resize)
        self.after(100, self._poll_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("App.TFrame", background="#f4f6f8")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), background="#f4f6f8")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 9), foreground="#667085")
        style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"), background="#ffffff")
        style.configure("Meta.TLabel", font=("Segoe UI", 9), foreground="#667085", background="#ffffff")
        style.configure("Badge.TLabel", font=("Segoe UI", 9, "bold"), foreground="#136c4a")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(18, 10))
        style.configure("Scene.TButton", padding=(10, 8))
        style.configure("Section.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8), anchor="w")
        style.configure(
            "ModeActive.TButton", font=("Segoe UI", 9, "bold"), foreground="#136c4a", background="#edf7f2"
        )
        style.configure(
            "KPI.TButton", font=("Segoe UI", 10), padding=(14, 10), anchor="w", background="#ffffff"
        )
        style.configure(
            "KPIActive.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10), anchor="w",
            background="#eaf2ff", foreground="#175cd3",
        )
        style.configure("Danger.TButton", foreground="#b42318", background="#fff4f2")

    def _build_ui(self) -> None:
        self.configure(background="#f4f6f8")
        outer = ttk.Frame(self, style="App.TFrame", padding=(18, 14))
        self.single_view = outer
        outer.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(outer, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(1, weight=1)
        ttk.Label(header, text="Studio video vẽ tay", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        self.project_header = ttk.Label(header, text="Chưa mở dự án", style="Subtitle.TLabel", anchor="w")
        self.project_header.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        ttk.Button(header, text="ĐƠN NHIỆM", style="ModeActive.TButton").grid(
            row=0, column=2, padx=(12, 0)
        )
        ttk.Button(header, text="MULTI JOB", command=self._show_multi_mode).grid(row=0, column=3)
        self.open_file_button = ttk.Button(header, text="Mở dự án", command=self._choose_project_file)
        self.open_file_button.grid(row=0, column=4, padx=(12, 8))
        self.render_button = ttk.Button(
            header, text="Tạo video", style="Accent.TButton", command=self._start_render, state="disabled"
        )
        self.render_button.grid(row=0, column=5)

        self.workspace = ttk.Frame(outer, style="App.TFrame")
        self.workspace.grid(row=1, column=0, sticky="nsew")
        self.preview_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=14)
        self.settings_card = ttk.Frame(self.workspace, style="Card.TFrame", padding=14)
        self._build_preview_card()
        self._build_settings_card()

        log_card = ttk.Frame(outer, style="Card.TFrame", padding=(12, 10))
        log_card.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        log_card.grid_columnconfigure(0, weight=1)
        ttk.Label(log_card, text="Nhật ký hoạt động", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 7)
        )
        self.log_text = tk.Text(
            log_card, height=6, wrap="word", state="disabled", relief="flat", padx=10, pady=8,
            font=("Consolas", 9), background="#17202a", foreground="#e8edf2", insertbackground="white",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_card, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=1, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self._apply_responsive_layout("horizontal")
        self.multi_view = MultiJobView(self)
        self.multi_view.grid(row=0, column=0, sticky="nsew")
        self.multi_view.grid_remove()

    def _show_single_mode(self) -> None:
        if hasattr(self, "multi_view"):
            self.multi_view.grid_remove()
            self.multi_view.video_player.pause()
        self.single_view.grid()

    def _show_multi_mode(self) -> None:
        self.single_view.grid_remove()
        if self.video_player:
            self.video_player.pause()
        self.multi_view.grid()
        self.multi_view.refresh()

    def _build_preview_card(self) -> None:
        self.preview_card.grid_rowconfigure(1, weight=1)
        self.preview_card.grid_columnconfigure(0, weight=1)
        top = ttk.Frame(self.preview_card, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)
        ttk.Label(top, text="Xem trước", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.scene_counter = ttk.Label(top, text="0 cảnh", style="Meta.TLabel")
        self.scene_counter.grid(row=0, column=1, sticky="e", padx=(8, 10))
        self.scene_preview_button = ttk.Button(top, text="Ảnh cảnh", command=self._show_scene_preview)
        self.scene_preview_button.grid(row=0, column=2, padx=(0, 5))
        self.result_preview_button = ttk.Button(
            top, text="Video kết quả", command=self._show_result_preview, state="disabled"
        )
        self.result_preview_button.grid(row=0, column=3)

        self.preview_canvas = tk.Canvas(
            self.preview_card, background="#e9edf2", highlightthickness=0, relief="flat", height=330
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew")
        self.preview_canvas.bind("<Configure>", self._schedule_preview)
        self.preview_canvas.bind("<Button-1>", self._preview_canvas_clicked)
        self.preview_canvas.create_text(
            0, 0, text="Mở một dự án để xem trước", fill="#667085", font=("Segoe UI", 11), tags="empty"
        )

        result_bar = ttk.Frame(self.preview_card, style="Card.TFrame")
        result_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        result_bar.grid_columnconfigure(2, weight=1)
        ttk.Label(result_bar, textvariable=self.result_path, style="Meta.TLabel").grid(
            row=0, column=0, columnspan=5, sticky="ew", pady=(0, 5)
        )
        self.play_result_button = ttk.Button(
            result_bar, text="▶ Phát", command=self._play_result, state="disabled", width=10
        )
        self.play_result_button.grid(row=1, column=0, padx=(0, 4))
        self.stop_result_button = ttk.Button(
            result_bar, text="■", command=self._stop_result, state="disabled", width=3
        )
        self.stop_result_button.grid(row=1, column=1, padx=(0, 6))
        self.video_seek_bar = ttk.Scale(
            result_bar, from_=0.0, to=1.0, variable=self.video_seek, state="disabled"
        )
        self.video_seek_bar.grid(row=1, column=2, sticky="ew")
        self.video_seek_bar.bind("<ButtonPress-1>", self._video_seek_started)
        self.video_seek_bar.bind("<ButtonRelease-1>", self._video_seek_finished)
        ttk.Label(result_bar, textvariable=self.video_time, style="Meta.TLabel").grid(
            row=1, column=3, padx=(8, 5)
        )
        self.external_result_button = ttk.Button(
            result_bar, text="↗", width=3, command=self._open_result_external, state="disabled"
        )
        self.external_result_button.grid(row=1, column=4)

        ttk.Label(self.preview_card, text="Danh sách cảnh", style="CardTitle.TLabel").grid(
            row=3, column=0, sticky="w", pady=(12, 7)
        )
        scene_table = ttk.Frame(self.preview_card, style="Card.TFrame")
        scene_table.grid(row=4, column=0, sticky="ew")
        scene_table.grid_columnconfigure(0, weight=1)
        self.scene_list = ttk.Treeview(
            scene_table, columns=("number", "title", "status"), show="headings", height=5, selectmode="browse"
        )
        self.scene_list.heading("number", text="#")
        self.scene_list.heading("title", text="Phân cảnh nội dung")
        self.scene_list.heading("status", text="Trạng thái")
        self.scene_list.column("number", width=42, minwidth=42, stretch=False, anchor="center")
        self.scene_list.column("title", width=310, minwidth=160, stretch=True)
        self.scene_list.column("status", width=90, minwidth=80, stretch=False, anchor="center")
        self.scene_list.grid(row=0, column=0, sticky="ew")
        self.scene_list.bind("<<TreeviewSelect>>", self._scene_list_selected)
        scene_scroll = ttk.Scrollbar(scene_table, orient="vertical", command=self.scene_list.yview)
        scene_scroll.grid(row=0, column=1, sticky="ns")
        self.scene_list.configure(yscrollcommand=scene_scroll.set)

    def _build_settings_card(self) -> None:
        self.settings_card.grid_columnconfigure(0, weight=1)
        self.settings_card.grid_rowconfigure(1, weight=1)
        ttk.Label(self.settings_card, text="Dự án từ GPT", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        project_info = ttk.LabelFrame(self.settings_card, text="Thông tin đã quét", padding=10)
        project_info.grid(row=1, column=0, sticky="nsew", pady=(10, 7))
        project_info.grid_columnconfigure(0, weight=1)
        project_info.grid_rowconfigure(4, weight=1)
        ttk.Label(project_info, textvariable=self.project_title_text, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(project_info, textvariable=self.project_meta_text, style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        ttk.Label(project_info, textvariable=self.project_source_text, style="Subtitle.TLabel").grid(
            row=2, column=0, sticky="ew", pady=(2, 6)
        )
        ttk.Label(project_info, text="Kịch bản lời đọc", style="Subtitle.TLabel").grid(
            row=3, column=0, sticky="w", pady=(2, 3)
        )
        script_box = ttk.Frame(project_info)
        script_box.grid(row=4, column=0, sticky="nsew")
        script_box.grid_rowconfigure(0, weight=1)
        script_box.grid_columnconfigure(0, weight=1)
        self.project_script = tk.Text(
            script_box, height=12, wrap="word", state="disabled", relief="solid", borderwidth=1,
            padx=9, pady=8, font=("Segoe UI", 10), background="#ffffff",
        )
        self.project_script.grid(row=0, column=0, sticky="nsew")
        script_scroll = ttk.Scrollbar(script_box, orient="vertical", command=self.project_script.yview)
        script_scroll.grid(row=0, column=1, sticky="ns")
        self.project_script.configure(yscrollcommand=script_scroll.set)

        self.video_settings_shell = ttk.Frame(self.settings_card, style="Card.TFrame")
        self.video_settings_shell.grid(row=2, column=0, sticky="ew", pady=7)
        self.video_settings_shell.grid_columnconfigure(0, weight=1)
        self.video_settings_toggle = ttk.Button(
            self.video_settings_shell,
            textvariable=self.video_settings_heading,
            style="Section.TButton",
            command=self._toggle_video_settings,
        )
        self.video_settings_toggle.grid(row=0, column=0, sticky="ew")

        video_settings = ttk.Frame(self.video_settings_shell, padding=(10, 10, 10, 4))
        self.video_settings_body = video_settings
        video_settings.grid_columnconfigure(1, weight=1)
        ttk.Label(video_settings, text="Giọng đọc", style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.voice_combo = ttk.Combobox(video_settings, textvariable=self.selected_voice_text, state="readonly")
        self.voice_combo.grid(row=0, column=1, sticky="ew")
        self.voice_combo.bind("<<ComboboxSelected>>", self._voice_selected)
        self.preview_voice_button = ttk.Button(video_settings, text="▶", width=3, command=self._preview_voice)
        self.preview_voice_button.grid(row=0, column=2, padx=(5, 2))
        self.stop_voice_button = ttk.Button(video_settings, text="■", width=3, command=stop_audio)
        self.stop_voice_button.grid(row=0, column=3, padx=2)
        self.voice_settings_button = ttk.Button(
            video_settings, text="⚙", width=3, command=self._open_voice_manager
        )
        self.voice_settings_button.grid(row=0, column=4, padx=(2, 0))

        ttk.Label(video_settings, text="Khung hình", style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=(10, 0)
        )
        ratio = ttk.Frame(video_settings)
        ratio.grid(row=1, column=1, columnspan=4, sticky="ew", pady=(10, 0))
        for column, (key, spec) in enumerate(ASPECT_RATIOS.items()):
            ratio.grid_columnconfigure(column, weight=1)
            ttk.Radiobutton(
                ratio, text=f"{key}  {spec.width}×{spec.height}", value=key,
                variable=self.aspect_ratio, command=self._schedule_preview,
            ).grid(row=0, column=column, sticky="w", padx=(0, 8))

        ttk.Label(video_settings, text="Chữ trên bút", style="Subtitle.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=(10, 0)
        )
        ttk.Entry(video_settings, textvariable=self.pen_brand).grid(
            row=2, column=1, columnspan=4, sticky="ew", pady=(10, 0)
        )

        ttk.Label(video_settings, text="Nơi lưu", style="Subtitle.TLabel").grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=(10, 0)
        )
        output = ttk.Frame(video_settings)
        output.grid(row=3, column=1, columnspan=4, sticky="ew", pady=(10, 0))
        output.grid_columnconfigure(0, weight=1)
        ttk.Label(output, textvariable=self.output_path, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self.output_button = ttk.Button(output, text="Chọn…", command=self._choose_output)
        self.output_button.grid(row=0, column=1)

        ttk.Label(video_settings, textvariable=self.timeline_text, style="Subtitle.TLabel").grid(
            row=4, column=0, columnspan=5, sticky="ew", pady=(8, 0)
        )

        status = ttk.Frame(self.settings_card, style="Card.TFrame")
        status.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        status.grid_columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.progress_text, style="Meta.TLabel").grid(row=0, column=0, sticky="w")
        self.cancel_button = ttk.Button(status, text="Hủy", command=self.cancel_event.set, state="disabled")
        self.cancel_button.grid(row=0, column=1)
        self.progress = ttk.Progressbar(status, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 0))

    def _toggle_video_settings(self) -> None:
        self.video_settings_expanded = not self.video_settings_expanded
        self.video_settings_heading.set(video_settings_heading(self.video_settings_expanded))
        if self.video_settings_expanded:
            self.video_settings_body.grid(row=1, column=0, sticky="ew")
        else:
            self.video_settings_body.grid_remove()

    def _on_window_resize(self, event: tk.Event) -> None:
        if event.widget is self:
            mode = responsive_layout(event.width)
            if mode != self._layout_mode:
                self._apply_responsive_layout(mode)

    def _apply_responsive_layout(self, mode: str) -> None:
        self.preview_card.grid_forget()
        self.settings_card.grid_forget()
        if mode == "horizontal":
            self.workspace.grid_columnconfigure(0, weight=3)
            self.workspace.grid_columnconfigure(1, weight=2)
            self.workspace.grid_rowconfigure(0, weight=1)
            self.workspace.grid_rowconfigure(1, weight=0)
            self.preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
            self.settings_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        else:
            self.workspace.grid_columnconfigure(0, weight=1)
            self.workspace.grid_columnconfigure(1, weight=0)
            self.workspace.grid_rowconfigure(0, weight=1)
            self.workspace.grid_rowconfigure(1, weight=0)
            self.preview_card.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
            self.settings_card.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._layout_mode = mode

    def _choose_project_file(self) -> None:
        source = filedialog.askopenfilename(
            title="Chọn project.json hoặc gói ZIP",
            filetypes=[("Dự án video", "project.json *.zip"), ("Tất cả file", "*.*")],
        )
        if source:
            self._open_project(source)

    def _choose_project_folder(self) -> None:
        source = filedialog.askdirectory(title="Chọn thư mục có project.json")
        if source:
            self._open_project(source)

    def _open_project(self, source: str) -> None:
        try:
            loaded = load_project(source)
        except ProjectError as exc:
            messagebox.showerror("Không thể mở dự án", str(exc), parent=self)
            return
        if self.project:
            self.project.close()
        if self.video_player:
            self.video_player.close()
        self.project = loaded
        self.output_dir = loaded.root / "output" if loaded.temporary_root is None else None
        preview_items = project_preview_items(loaded)
        item_count = len(preview_items)
        self.project_header.configure(
            text=f"{loaded.title}  •  phiên bản {loaded.version}  •  {item_count} phân cảnh"
        )
        self.scene_counter.configure(text=f"{item_count} phân cảnh")
        self.output_path.set(str(self.output_dir) if self.output_dir else "Chọn nơi xuất cho dự án ZIP")
        self.pen_brand.set(loaded.pen_brand or "Ăn dặm mẹ Dâu")
        total_ms = sum(scene.duration_ms for scene in loaded.scenes)
        duration_text = f"{total_ms / 1000:.1f} giây" if total_ms else "chưa có thời lượng"
        self.project_title_text.set(loaded.title)
        self.project_meta_text.set(
            f"{item_count} phân cảnh  •  {len(loaded.scenes)} ảnh nguồn  •  {duration_text}  •  phiên bản {loaded.version}"
        )
        self.project_source_text.set(f"Nguồn: {loaded.manifest_path.name}")
        self.project_script.configure(state="normal")
        self.project_script.delete("1.0", "end")
        self.project_script.insert(
            "1.0", loaded.script_text or "Gói dự án chưa có script.txt hoặc trường script trong project.json."
        )
        self.project_script.configure(state="disabled")
        self.voice_path.set(str(loaded.voice) if loaded.voice else "Chưa tạo âm thanh — hãy chạy OmniVoice")
        self.timeline_text.set(
            f"Timeline: {len(loaded.narration_cues)} cue chờ tạo voice"
            if loaded.narration_cues
            else "Timeline: dự án cũ chưa có narration cue"
        )
        self._preview_items.clear()
        for row in self.scene_list.get_children():
            self.scene_list.delete(row)
        for index, item in enumerate(preview_items, start=1):
            row_id = f"preview-{index}"
            self._preview_items[row_id] = item
            self.scene_list.insert("", "end", iid=row_id, values=(f"{index:02d}", item.title, "Sẵn sàng"))
        self._append_log(f"Đã mở dự án: {loaded.title}")
        self._append_log(f"Nguồn: {loaded.manifest_path}")
        if loaded.script_path:
            self._append_log(f"Kịch bản: {loaded.script_path.name}")
        else:
            self._append_log("CẢNH BÁO: Gói dự án chưa có kịch bản để tạo voice.")
        self.render_button.configure(state="normal")
        self.progress_text.set("Sẵn sàng — bấm Tạo video để chạy toàn bộ quy trình")
        self._final_video = None
        self._final_poster = None
        self._final_preview_audio = None
        self.result_path.set("Chưa có video kết quả")
        self.result_preview_button.configure(state="disabled")
        self._set_result_controls(False)
        self.video_seek.set(0.0)
        self.video_time.set("00:00 / 00:00")
        if self.output_dir:
            existing_video = self.output_dir / "final.mp4"
            if existing_video.is_file():
                self._final_video = existing_video
                existing_poster = self.output_dir / "preview.jpg"
                self._final_poster = existing_poster if existing_poster.is_file() else None
                self._final_preview_audio = next(
                    (
                        candidate
                        for candidate in (
                            self.output_dir / "preview-audio.wav",
                            self.output_dir / "voice-timeline.wav",
                            self.output_dir / "voice-clone.wav",
                        )
                        if candidate.is_file()
                    ),
                    None,
                )
                self.result_path.set(f"Video: {existing_video.name}")
                self.result_preview_button.configure(state="normal")
                self._set_result_controls(True)
        first_row = self.scene_list.get_children()[0]
        self.scene_list.selection_set(first_row)
        self.scene_list.focus(first_row)
        self._select_preview_item(self._preview_items[first_row])

    def _select_scene(self, scene: Scene) -> None:
        self._select_preview_item(PreviewItem(scene.scene_id, scene.title, scene))

    def _scene_list_selected(self, _event: tk.Event | None = None) -> None:
        selected = self.scene_list.selection()
        if selected and selected[0] in self._preview_items:
            self._select_preview_item(self._preview_items[selected[0]])

    def _select_preview_item(self, item: PreviewItem) -> None:
        self._active_preview_item = item
        self._preview_kind = "scene"
        if self.video_player and self.video_player.state == "playing":
            self.video_player.pause()
        self.preview_canvas.configure(background="#e9edf2")
        try:
            from PIL import Image
            with Image.open(item.scene.image) as source:
                image = source.convert("RGB")
                if item.region:
                    x1, y1, x2, y2 = item.region
                    padding = max(12, round(min(image.size) * 0.02))
                    crop = (
                        max(0, x1 - padding), max(0, y1 - padding),
                        min(image.width, x2 + padding), min(image.height, y2 + padding),
                    )
                    image = image.crop(crop)
                self._preview_image = image
            self._render_preview()
        except Exception as exc:
            self._preview_image = None
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                max(1, self.preview_canvas.winfo_width() // 2), max(1, self.preview_canvas.winfo_height() // 2),
                text=f"Không thể xem trước ảnh\n{exc}", justify="center", fill="#667085",
            )

    def _show_scene_preview(self) -> None:
        if self._active_preview_item:
            self._select_preview_item(self._active_preview_item)

    def _show_result_preview(self) -> None:
        if not self._final_video:
            return
        self._preview_kind = "result"
        try:
            if self.video_player is None:
                raise VideoPlaybackError("Trình phát nội bộ chưa được khởi tạo.")
            if self.video_player.path != self._final_video:
                self.video_player.load(self._final_video, self._final_preview_audio)
            else:
                self.video_player.redraw()
            self._set_result_controls(True)
        except VideoPlaybackError as exc:
            self._append_log(f"Trình phát nội bộ: {exc}")
            self._show_result_poster_fallback()

    def _play_result(self) -> None:
        if not self._final_video or not self._final_video.is_file():
            messagebox.showwarning("Chưa có video", "Hãy tạo video trước khi xem kết quả.", parent=self)
            return
        self._show_result_preview()
        if self.video_player and self.video_player.loaded:
            self.video_player.play_pause()

    def _stop_result(self) -> None:
        if self.video_player:
            self.video_player.stop()

    def _open_result_external(self) -> None:
        if not self._final_video or not self._final_video.is_file():
            return
        try:
            open_media(self._final_video)
        except OSError as exc:
            messagebox.showerror("Không thể mở video", str(exc), parent=self)

    def _preview_canvas_clicked(self, _event: tk.Event | None = None) -> None:
        if self._preview_kind == "result":
            self._play_result()

    def _show_result_poster_fallback(self) -> None:
        self._preview_image = None
        if self._final_poster and self._final_poster.is_file():
            try:
                from PIL import Image
                with Image.open(self._final_poster) as source:
                    self._preview_image = source.convert("RGB")
            except Exception as exc:
                self._append_log(f"Không đọc được ảnh xem trước video: {exc}")
        self._render_preview()
        self.external_result_button.configure(state="normal")

    def _set_result_controls(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.play_result_button.configure(state=state)
        self.stop_result_button.configure(state=state)
        self.video_seek_bar.configure(state=state)
        self.external_result_button.configure(state=state)

    def _video_position_changed(self, position: float, duration: float) -> None:
        if not self._seeking_video:
            self.video_seek_bar.configure(to=max(0.01, duration))
            self.video_seek.set(position)
        self.video_time.set(f"{format_media_time(position)} / {format_media_time(duration)}")

    def _video_state_changed(self, state: str) -> None:
        self.play_result_button.configure(text="⏸ Tạm dừng" if state == "playing" else "▶ Phát")

    def _video_error(self, message: str) -> None:
        self._append_log(message)
        self.progress_text.set("Lỗi trình phát — có thể dùng nút ↗ để mở ngoài")

    def _video_seek_started(self, _event: tk.Event | None = None) -> None:
        self._seeking_video = True

    def _video_seek_finished(self, _event: tk.Event | None = None) -> None:
        self._seeking_video = False
        if self.video_player and self.video_player.loaded:
            self.video_player.seek(float(self.video_seek.get()))

    def _mark_scene_status(self, status: str) -> None:
        for row_id in self.scene_list.get_children():
            values = list(self.scene_list.item(row_id, "values"))
            if len(values) >= 3:
                values[2] = status
                self.scene_list.item(row_id, values=values)

    def _schedule_preview(self, _event: tk.Event | None = None) -> None:
        if self._preview_after:
            self.after_cancel(self._preview_after)
        self._preview_after = self.after(80, self._render_preview)

    def _render_preview(self) -> None:
        self._preview_after = None
        width = max(1, self.preview_canvas.winfo_width())
        height = max(1, self.preview_canvas.winfo_height())
        if self._preview_kind == "result" and self.video_player and self.video_player.loaded:
            self.video_player.redraw()
            return
        if self._preview_image is None:
            self.preview_canvas.delete("all")
            label = (
                "▶ Video đã sẵn sàng\nBấm vào đây hoặc nút Phát video để xem"
                if self._preview_kind == "result"
                else "Mở một dự án để xem trước"
            )
            self.preview_canvas.create_text(
                width // 2, height // 2, text=label, justify="center",
                fill="#667085", font=("Segoe UI", 11), tags="empty",
            )
            return
        try:
            from PIL import ImageOps, ImageTk
            canvas_width, canvas_height = max(80, width - 28), max(80, height - 28)
            spec = ASPECT_RATIOS[self.aspect_ratio.get()]
            target_width = min(canvas_width, int(canvas_height * spec.width / spec.height))
            target_height = int(target_width * spec.height / spec.width)
            if target_height > canvas_height:
                target_height = canvas_height
                target_width = int(target_height * spec.width / spec.height)
            preview = ImageOps.fit(self._preview_image, (max(1, target_width), max(1, target_height)))
            self._preview_photo = ImageTk.PhotoImage(preview)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(width // 2, height // 2, image=self._preview_photo, anchor="center")
            if self._preview_kind == "result":
                self.preview_canvas.create_text(
                    width // 2, height // 2, text="▶", fill="white", font=("Segoe UI", 38, "bold")
                )
                self.preview_canvas.create_text(
                    width // 2, height // 2 + 50, text="Bấm để phát video", fill="white",
                    font=("Segoe UI", 10, "bold"),
                )
        except Exception as exc:
            self._append_log(f"Không thể cập nhật xem trước: {exc}")

    def _refresh_voice_profiles(self) -> None:
        self._voice_profile_options = [
            profile for profile in self.voice_library.profiles if profile.audio_path.is_file()
        ]
        values = [
            f"{profile.name}  •  {profile.duration_seconds:.1f}s  •  {profile.quality_score}/100"
            for profile in self._voice_profile_options
        ]
        self.voice_combo.configure(values=values)
        settings = VoiceSettings.load()
        selected_index = next(
            (
                index
                for index, profile in enumerate(self._voice_profile_options)
                if profile.profile_id == settings.selected_profile_id
            ),
            0 if self._voice_profile_options else -1,
        )
        if selected_index >= 0:
            self.voice_combo.current(selected_index)
            self.selected_voice_text.set(values[selected_index])
        else:
            self.voice_combo.set("Chưa có giọng — mở Cài đặt giọng để thêm")

    def _selected_voice_profile(self) -> VoiceProfile | None:
        index = self.voice_combo.current()
        if 0 <= index < len(self._voice_profile_options):
            return self._voice_profile_options[index]
        return None

    def _voice_selected(self, _event: tk.Event | None = None) -> None:
        profile = self._selected_voice_profile()
        if not profile:
            return
        settings = VoiceSettings.load()
        VoiceSettings(cli_path=settings.cli_path, selected_profile_id=profile.profile_id).save()
        self._append_log(f"Đã chọn giọng: {profile.name} ({profile.quality_score}/100)")

    def _preview_voice(self) -> None:
        profile = self._selected_voice_profile()
        if not profile:
            messagebox.showinfo("Chưa có giọng", "Mở Cài đặt giọng để thêm và làm sạch mẫu.", parent=self)
            return
        try:
            play_audio(profile.audio_path)
        except OmniVoiceError as exc:
            messagebox.showerror("Không thể nghe thử", str(exc), parent=self)

    def _open_voice_manager(self) -> None:
        VoiceManagerDialog(
            self,
            library=self.voice_library,
            on_library_changed=self._refresh_voice_profiles,
            on_log=self._append_log,
        )

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory(title="Chọn thư mục xuất video")
        if selected:
            self.output_dir = Path(selected).resolve()
            self.output_path.set(str(self.output_dir))
            self._append_log(f"Thư mục xuất: {self.output_dir}")

    def _start_render(self) -> None:
        if not self.project:
            return
        project = self.project
        text = project.script_text.strip() or " ".join(cue.text for cue in project.narration_cues)
        profile = self._selected_voice_profile()
        cli = VoiceSettings.load().cli_path.strip()
        if (project.narration_cues or text) and (not profile or not cli):
            messagebox.showwarning(
                "Thiếu giọng đọc",
                "Hãy chọn một giọng đã lưu. Nếu chưa có, bấm nút ⚙ trong Thiết lập video.",
                parent=self,
            )
            return
        if not project.narration_cues and not text and not project.voice:
            messagebox.showwarning("Thiếu kịch bản", "Dự án chưa có nội dung để tạo giọng đọc.", parent=self)
            return
        if self.output_dir is None:
            self._choose_output()
        if self.output_dir is None:
            return
        brand = self.pen_brand.get().strip()
        if len(brand) > 40:
            messagebox.showwarning("Chữ trên bút quá dài", "Chỉ nhập tối đa 40 ký tự.", parent=self)
            return
        project.pen_brand = brand or None
        final = self.output_dir / "final.mp4"
        if final.exists() and not messagebox.askyesno(
            "Ghi đè video", f"{final} đã tồn tại. Bạn có muốn ghi đè?", parent=self
        ):
            return
        if self.video_player:
            self.video_player.close()
        self._set_result_controls(False)
        self.cancel_event.clear()
        self._mark_scene_status("Đang xử lý")
        self._set_busy(True, "Bước 1/3 — đang tạo giọng đọc…")
        output_dir, aspect_ratio = self.output_dir, self.aspect_ratio.get()

        def worker() -> None:
            try:
                log = lambda line: self.events.put(("log", line))
                if project.narration_cues:
                    assert profile is not None
                    cue_audio = generate_cue_voices(
                        cli_path=cli,
                        cues=project.narration_cues,
                        reference_audio=profile.audio_path,
                        output_dir=output_dir / "audio-cues",
                        on_log=log,
                        cancel_event=self.cancel_event,
                    )
                    self.events.put(("stage", "Bước 2/3 — đang đồng bộ voice với hình ảnh…"))
                    timeline = compile_timeline(project, cue_audio, output_dir, log)
                    project.voice = timeline.voice_path
                    project.runtime_annotations = timeline.runtime_annotations
                    self.events.put(("pipeline_timeline", timeline))
                elif text:
                    assert profile is not None
                    voice_output = output_dir / "voice-clone.wav"
                    result_voice = generate_clone_voice(
                        cli_path=cli,
                        text=text,
                        reference_audio=profile.audio_path,
                        output=voice_output,
                        on_log=log,
                        cancel_event=self.cancel_event,
                    )
                    project.voice = result_voice
                    self.events.put(("pipeline_voice", result_voice))
                self.events.put(("stage", "Bước 3/3 — đang dựng và ghép video…"))
                result = run_pipeline(
                    project, output_dir, log, self.cancel_event, aspect_ratio=aspect_ratio,
                )
                poster = create_video_poster(result, output_dir / "preview.jpg", log)
                preview_audio = create_video_preview_audio(
                    result, output_dir / "preview-audio.wav", log
                )
                self.events.put(("done", (result, poster, preview_audio)))
            except (OmniVoiceError, TimelineError, RenderError, OSError) as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _set_busy(self, busy: bool, label: str = "Sẵn sàng") -> None:
        state = "disabled" if busy else "normal"
        for control in (
            self.open_file_button, self.output_button,
            self.preview_voice_button, self.stop_voice_button, self.voice_settings_button,
        ):
            control.configure(state=state)
        self.voice_combo.configure(state="disabled" if busy else "readonly")
        render_ready = bool(self.project)
        self.render_button.configure(state="normal" if not busy and render_ready else "disabled")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        self.progress_text.set(label)
        self.progress.start(12) if busy else self.progress.stop()

    def _append_log(self, line: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "stage":
                    self.progress_text.set(str(payload))
                elif kind == "pipeline_voice":
                    self.voice_path.set(str(payload))
                    self.timeline_text.set("Voice đã tạo • dự án cũ không có narration cue")
                    self._append_log(f"Hoàn tất voice clone: {payload}")
                elif kind == "pipeline_timeline":
                    timeline = payload
                    assert isinstance(timeline, TimelineResult)
                    self.voice_path.set(str(timeline.voice_path))
                    self.timeline_text.set(
                        f"Timeline: {len(timeline.cues)} cue • {timeline.total_duration_ms / 1000:.1f} giây"
                    )
                    self._mark_scene_status("Đã đồng bộ")
                    self._append_log(f"Timeline: {timeline.timeline_path}")
                elif kind == "done":
                    self._set_busy(False, "Đã tạo video")
                    result, poster, preview_audio = payload
                    self._final_video = Path(result)
                    self._final_poster = Path(poster) if poster else None
                    self._final_preview_audio = Path(preview_audio) if preview_audio else None
                    self.result_path.set(f"Video: {self._final_video.name}")
                    self.result_preview_button.configure(state="normal")
                    self._set_result_controls(True)
                    self._mark_scene_status("Đã dựng")
                    self._append_log(f"Hoàn tất: {self._final_video}")
                    self._show_result_preview()
                    messagebox.showinfo(
                        "Hoàn tất",
                        f"Video đã được tạo tại:\n{self._final_video}\n\nBấm Phát ở cột bên trái để xem ngay trong app.",
                        parent=self,
                    )
                elif kind == "error":
                    self._set_busy(False, "Có lỗi — xem nhật ký phía dưới")
                    self._mark_scene_status("Có lỗi")
                    self._append_log(f"LỖI: {payload}")
                    messagebox.showerror("Tác vụ thất bại", str(payload), parent=self)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _on_close(self) -> None:
        self.cancel_event.set()
        if hasattr(self, "multi_view"):
            self.multi_view.close()
        if self.video_player:
            self.video_player.close()
        if self.project:
            self.project.close()
        self.destroy()


def main() -> None:
    WhiteboardApp().mainloop()
