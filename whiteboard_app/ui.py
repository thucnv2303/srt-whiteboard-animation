from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .project import ProjectError, Scene, VideoProject, load_project
from .renderer import ASPECT_RATIOS, RenderError, run_pipeline
from .timeline import TimelineError, TimelineResult, compile_timeline
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

        self.aspect_ratio = tk.StringVar(value="16:9")
        self.pen_brand = tk.StringVar(value="Ăn dặm mẹ Dâu")
        self.project_title_text = tk.StringVar(value="Chưa có dự án")
        self.project_meta_text = tk.StringVar(value="0 cảnh  •  chưa có thời lượng")
        self.project_source_text = tk.StringVar(value="GPT sẽ gửi ảnh và kịch bản vào gói dự án")
        self.voice_path = tk.StringVar(value="Chưa tạo âm thanh")
        self.timeline_text = tk.StringVar(value="Timeline: chưa đồng bộ")
        self.selected_voice_text = tk.StringVar(value="Chưa có giọng đã lưu")
        self.output_path = tk.StringVar(value="Tự động: thư mục output của dự án")
        self.progress_text = tk.StringVar(value="Sẵn sàng")

        self._build_styles()
        self._build_ui()
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

    def _build_ui(self) -> None:
        self.configure(background="#f4f6f8")
        outer = ttk.Frame(self, style="App.TFrame", padding=(18, 14))
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
        ttk.Label(header, text="ĐƠN NHIỆM", style="Badge.TLabel", padding=(10, 5)).grid(
            row=0, column=2, padx=(12, 8)
        )
        self.open_file_button = ttk.Button(header, text="Mở dự án", command=self._choose_project_file)
        self.open_file_button.grid(row=0, column=3, padx=(0, 8))
        self.render_button = ttk.Button(
            header, text="Tạo video", style="Accent.TButton", command=self._start_render, state="disabled"
        )
        self.render_button.grid(row=0, column=4)

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

    def _build_preview_card(self) -> None:
        self.preview_card.grid_rowconfigure(1, weight=1)
        self.preview_card.grid_columnconfigure(0, weight=1)
        top = ttk.Frame(self.preview_card, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)
        ttk.Label(top, text="Xem trước cảnh", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.scene_counter = ttk.Label(top, text="0 cảnh", style="Meta.TLabel")
        self.scene_counter.grid(row=0, column=1, sticky="e")

        self.preview_canvas = tk.Canvas(
            self.preview_card, background="#e9edf2", highlightthickness=0, relief="flat", height=370
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew")
        self.preview_canvas.bind("<Configure>", self._schedule_preview)
        self.preview_canvas.create_text(
            0, 0, text="Mở một dự án để xem trước", fill="#667085", font=("Segoe UI", 11), tags="empty"
        )

        ttk.Label(self.preview_card, text="Danh sách cảnh", style="CardTitle.TLabel").grid(
            row=2, column=0, sticky="w", pady=(12, 7)
        )
        scene_canvas = tk.Canvas(self.preview_card, height=76, background="#ffffff", highlightthickness=0)
        scene_canvas.grid(row=3, column=0, sticky="ew")
        scene_scroll = ttk.Scrollbar(self.preview_card, orient="horizontal", command=scene_canvas.xview)
        scene_scroll.grid(row=4, column=0, sticky="ew", pady=(4, 0))
        scene_canvas.configure(xscrollcommand=scene_scroll.set)
        self.scene_strip = ttk.Frame(scene_canvas, style="Card.TFrame")
        scene_window = scene_canvas.create_window((0, 0), window=self.scene_strip, anchor="nw")
        self.scene_strip.bind(
            "<Configure>", lambda _event: scene_canvas.configure(scrollregion=scene_canvas.bbox("all"))
        )
        scene_canvas.bind(
            "<Configure>", lambda event: scene_canvas.itemconfigure(scene_window, height=event.height)
        )

    def _build_settings_card(self) -> None:
        self.settings_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.settings_card, text="Dự án từ GPT", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        project_info = ttk.LabelFrame(self.settings_card, text="Thông tin đã quét", padding=10)
        project_info.grid(row=1, column=0, sticky="ew", pady=(10, 7))
        project_info.grid_columnconfigure(0, weight=1)
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
        self.project_script = tk.Text(
            project_info, height=5, wrap="word", state="disabled", relief="solid", borderwidth=1,
            padx=7, pady=6, font=("Segoe UI", 9), background="#ffffff",
        )
        self.project_script.grid(row=4, column=0, sticky="ew")

        audio = ttk.LabelFrame(self.settings_card, text="Giọng đọc", padding=10)
        audio.grid(row=2, column=0, sticky="ew", pady=7)
        audio.grid_columnconfigure(0, weight=1)
        ttk.Label(audio, textvariable=self.voice_path, style="Subtitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="ew", pady=(0, 6)
        )
        self.voice_combo = ttk.Combobox(audio, textvariable=self.selected_voice_text, state="readonly")
        self.voice_combo.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.voice_combo.bind("<<ComboboxSelected>>", self._voice_selected)
        self.preview_voice_button = ttk.Button(audio, text="▶ Nghe thử", command=self._preview_voice)
        self.preview_voice_button.grid(row=2, column=0, sticky="ew", pady=(7, 0), padx=(0, 4))
        ttk.Button(audio, text="■ Dừng", command=stop_audio).grid(
            row=2, column=1, sticky="ew", pady=(7, 0), padx=4
        )
        self.voice_settings_button = ttk.Button(audio, text="⚙ Cài đặt giọng…", command=self._open_voice_manager)
        self.voice_settings_button.grid(row=2, column=2, columnspan=2, sticky="ew", pady=(7, 0), padx=(4, 0))
        self.clone_button = ttk.Button(
            audio, text="Tạo âm thanh và đồng bộ timeline", command=self._start_voice_clone
        )
        self.clone_button.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Label(audio, textvariable=self.timeline_text, style="Subtitle.TLabel").grid(
            row=4, column=0, columnspan=4, sticky="ew", pady=(6, 0)
        )

        ratio = ttk.LabelFrame(self.settings_card, text="Tỷ lệ đầu ra", padding=10)
        ratio.grid(row=3, column=0, sticky="ew", pady=7)
        for column, (key, spec) in enumerate(ASPECT_RATIOS.items()):
            ratio.grid_columnconfigure(column, weight=1)
            ttk.Radiobutton(
                ratio, text=f"{key}\n{spec.width}×{spec.height}", value=key,
                variable=self.aspect_ratio, command=self._schedule_preview,
            ).grid(row=0, column=column, sticky="ew", padx=3)

        pen = ttk.LabelFrame(self.settings_card, text="Chữ trên thân bút", padding=10)
        pen.grid(row=4, column=0, sticky="ew", pady=7)
        pen.grid_columnconfigure(0, weight=1)
        ttk.Entry(pen, textvariable=self.pen_brand).grid(row=0, column=0, sticky="ew")
        ttk.Label(pen, text="Tối đa 40 ký tự", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))

        output = ttk.LabelFrame(self.settings_card, text="Nơi xuất", padding=10)
        output.grid(row=5, column=0, sticky="ew", pady=7)
        output.grid_columnconfigure(0, weight=1)
        ttk.Label(output, textvariable=self.output_path, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self.output_button = ttk.Button(output, text="Chọn…", command=self._choose_output)
        self.output_button.grid(row=0, column=1)

        status = ttk.Frame(self.settings_card, style="Card.TFrame")
        status.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        status.grid_columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.progress_text, style="Meta.TLabel").grid(row=0, column=0, sticky="w")
        self.cancel_button = ttk.Button(status, text="Hủy", command=self.cancel_event.set, state="disabled")
        self.cancel_button.grid(row=0, column=1)
        self.progress = ttk.Progressbar(status, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 0))

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
        self.project = loaded
        self.output_dir = loaded.root / "output" if loaded.temporary_root is None else None
        self.project_header.configure(text=f"{loaded.title}  •  phiên bản {loaded.version}  •  {len(loaded.scenes)} cảnh")
        self.scene_counter.configure(text=f"{len(loaded.scenes)} cảnh")
        self.output_path.set(str(self.output_dir) if self.output_dir else "Chọn nơi xuất cho dự án ZIP")
        self.pen_brand.set(loaded.pen_brand or "Ăn dặm mẹ Dâu")
        total_ms = sum(scene.duration_ms for scene in loaded.scenes)
        duration_text = f"{total_ms / 1000:.1f} giây" if total_ms else "chưa có thời lượng"
        self.project_title_text.set(loaded.title)
        self.project_meta_text.set(f"{len(loaded.scenes)} cảnh  •  {duration_text}  •  phiên bản {loaded.version}")
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
        for child in self.scene_strip.winfo_children():
            child.destroy()
        for index, scene in enumerate(loaded.scenes, start=1):
            ttk.Button(
                self.scene_strip, text=f"{index:02d}  {scene.title}", style="Scene.TButton",
                command=lambda selected=scene: self._select_scene(selected),
            ).grid(row=0, column=index - 1, padx=(0, 7), sticky="ns")
        self._append_log(f"Đã mở dự án: {loaded.title}")
        self._append_log(f"Nguồn: {loaded.manifest_path}")
        if loaded.script_path:
            self._append_log(f"Kịch bản: {loaded.script_path.name}")
        else:
            self._append_log("CẢNH BÁO: Gói dự án chưa có kịch bản để tạo voice.")
        self.render_button.configure(state="normal" if loaded.voice else "disabled")
        self.progress_text.set(
            "Đã có âm thanh — sẵn sàng dựng" if loaded.voice else "Bước tiếp theo: tạo âm thanh bằng OmniVoice"
        )
        self._select_scene(loaded.scenes[0])

    def _select_scene(self, scene: Scene) -> None:
        try:
            from PIL import Image
            with Image.open(scene.image) as source:
                self._preview_image = source.convert("RGB")
            self._render_preview()
        except Exception as exc:
            self._preview_image = None
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                max(1, self.preview_canvas.winfo_width() // 2), max(1, self.preview_canvas.winfo_height() // 2),
                text=f"Không thể xem trước ảnh\n{exc}", justify="center", fill="#667085",
            )

    def _schedule_preview(self, _event: tk.Event | None = None) -> None:
        if self._preview_after:
            self.after_cancel(self._preview_after)
        self._preview_after = self.after(80, self._render_preview)

    def _render_preview(self) -> None:
        self._preview_after = None
        width = max(1, self.preview_canvas.winfo_width())
        height = max(1, self.preview_canvas.winfo_height())
        if self._preview_image is None:
            self.preview_canvas.coords("empty", width // 2, height // 2)
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

    def _start_voice_clone(self) -> None:
        if not self.project:
            messagebox.showwarning("Chưa có dự án", "Hãy mở dự án trước khi tạo voice.", parent=self)
            return
        project = self.project
        text = project.script_text.strip() or " ".join(cue.text for cue in project.narration_cues)
        profile = self._selected_voice_profile()
        cli = VoiceSettings.load().cli_path.strip()
        if not text or not profile or not cli:
            messagebox.showwarning(
                "Thiếu thông tin",
                "Gói dự án phải có kịch bản. Hãy chọn một giọng đã lưu; nếu chưa có, mở Cài đặt giọng.",
                parent=self,
            )
            return
        output_root = self.output_dir or project.root
        voice_output = output_root / "voice-clone.wav"
        self.cancel_event.clear()
        self._set_busy(True, f"Đang tạo âm thanh bằng giọng {profile.name}…")

        def worker() -> None:
            try:
                log = lambda line: self.events.put(("log", line))
                if project.narration_cues:
                    cue_audio = generate_cue_voices(
                        cli_path=cli,
                        cues=project.narration_cues,
                        reference_audio=profile.audio_path,
                        output_dir=output_root / "audio-cues",
                        on_log=log,
                        cancel_event=self.cancel_event,
                    )
                    timeline = compile_timeline(project, cue_audio, output_root, log)
                    self.events.put(("timeline_done", timeline))
                else:
                    result = generate_clone_voice(
                        cli_path=cli, text=text, reference_audio=profile.audio_path, output=voice_output,
                        on_log=log, cancel_event=self.cancel_event,
                    )
                    self.events.put(("voice_done", result))
            except (OmniVoiceError, TimelineError, OSError) as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory(title="Chọn thư mục xuất video")
        if selected:
            self.output_dir = Path(selected).resolve()
            self.output_path.set(str(self.output_dir))
            self._append_log(f"Thư mục xuất: {self.output_dir}")

    def _start_render(self) -> None:
        if not self.project:
            return
        if not self.project.voice:
            messagebox.showwarning(
                "Chưa có âm thanh", "Hãy tạo âm thanh bằng OmniVoice trước khi dựng video.", parent=self
            )
            return
        if self.output_dir is None:
            self._choose_output()
        if self.output_dir is None:
            return
        brand = self.pen_brand.get().strip()
        if len(brand) > 40:
            messagebox.showwarning("Chữ trên bút quá dài", "Chỉ nhập tối đa 40 ký tự.", parent=self)
            return
        self.project.pen_brand = brand or None
        final = self.output_dir / "final.mp4"
        if final.exists() and not messagebox.askyesno(
            "Ghi đè video", f"{final} đã tồn tại. Bạn có muốn ghi đè?", parent=self
        ):
            return
        self.cancel_event.clear()
        self._set_busy(True, "Đang dựng video…")
        project, output_dir, aspect_ratio = self.project, self.output_dir, self.aspect_ratio.get()

        def worker() -> None:
            try:
                result = run_pipeline(
                    project, output_dir, lambda line: self.events.put(("log", line)),
                    self.cancel_event, aspect_ratio=aspect_ratio,
                )
                self.events.put(("done", result))
            except (RenderError, OSError) as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _set_busy(self, busy: bool, label: str = "Sẵn sàng") -> None:
        state = "disabled" if busy else "normal"
        for control in (
            self.open_file_button, self.output_button,
            self.preview_voice_button, self.voice_settings_button, self.clone_button,
        ):
            control.configure(state=state)
        self.voice_combo.configure(state="disabled" if busy else "readonly")
        render_ready = bool(self.project and self.project.voice)
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
                elif kind == "voice_done":
                    self._set_busy(False, "Voice clone đã sẵn sàng")
                    assert self.project is not None
                    self.project.voice = Path(payload)
                    self.voice_path.set(str(payload))
                    self.render_button.configure(state="normal")
                    self._append_log(f"Hoàn tất voice clone: {payload}")
                elif kind == "timeline_done":
                    self._set_busy(False, "Voice và hình ảnh đã đồng bộ")
                    assert self.project is not None
                    timeline = payload
                    assert isinstance(timeline, TimelineResult)
                    self.project.voice = timeline.voice_path
                    self.project.runtime_annotations = timeline.runtime_annotations
                    self.voice_path.set(str(timeline.voice_path))
                    self.timeline_text.set(
                        f"Timeline: {len(timeline.cues)} cue • {timeline.total_duration_ms / 1000:.1f} giây"
                    )
                    self.render_button.configure(state="normal")
                    self._append_log(f"Timeline: {timeline.timeline_path}")
                elif kind == "done":
                    self._set_busy(False, "Đã tạo video")
                    self._append_log(f"Hoàn tất: {payload}")
                    messagebox.showinfo("Hoàn tất", f"Video đã được tạo tại:\n{payload}", parent=self)
                elif kind == "error":
                    self._set_busy(False, "Có lỗi — xem nhật ký phía dưới")
                    self._append_log(f"LỖI: {payload}")
                    messagebox.showerror("Tác vụ thất bại", str(payload), parent=self)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _on_close(self) -> None:
        self.cancel_event.set()
        if self.project:
            self.project.close()
        self.destroy()


def main() -> None:
    WhiteboardApp().mainloop()
