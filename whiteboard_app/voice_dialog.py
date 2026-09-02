from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from .voice import (
    OmniVoiceError,
    VoiceLibrary,
    VoiceSettings,
    play_audio,
    prepare_voice_profile,
    stop_audio,
)


class VoiceManagerDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        library: VoiceLibrary,
        on_library_changed: Callable[[], None],
        on_log: Callable[[str], None],
    ) -> None:
        super().__init__(parent)
        self.title("Cài đặt và quản lý giọng đọc")
        self.geometry("760x610")
        self.minsize(680, 560)
        self.transient(parent)
        self.library = library
        self.on_library_changed = on_library_changed
        self.on_log = on_log
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        settings = VoiceSettings.load()
        self.cli_path = tk.StringVar(value=settings.cli_path)
        self.profile_name = tk.StringVar(value="")
        self.source_path = tk.StringVar(value="Chưa chọn file ghi âm")
        self.status_text = tk.StringVar(value="Chọn mẫu giọng sạch, chỉ có một người nói.")
        self._build_ui()
        self._refresh_profiles()
        self.after(100, self._poll_events)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(2, weight=1)

        ttk.Label(outer, text="Cài đặt giọng đọc", font=("Segoe UI", 17, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            outer,
            text="OmniVoice chỉ cài một lần; mỗi giọng mẫu đã làm sạch được dùng lại cho mọi dự án.",
            foreground="#667085",
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))

        body = ttk.Frame(outer)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        engine = ttk.LabelFrame(body, text="OmniVoice dùng chung", padding=10)
        engine.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        engine.grid_columnconfigure(0, weight=1)
        ttk.Entry(engine, textvariable=self.cli_path).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(engine, text="Chọn omnivoice-infer.exe…", command=self._choose_cli).grid(row=0, column=1)
        ttk.Button(engine, text="Lưu", command=self._save_cli_settings).grid(
            row=0, column=2, padx=(8, 0)
        )

        library_frame = ttk.LabelFrame(body, text="Thư viện giọng đã xử lý", padding=10)
        library_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        library_frame.grid_columnconfigure(0, weight=1)
        library_frame.grid_rowconfigure(0, weight=1)
        self.profile_tree = ttk.Treeview(
            library_frame, columns=("name", "duration", "quality"), show="headings", height=6
        )
        self.profile_tree.heading("name", text="Tên giọng")
        self.profile_tree.heading("duration", text="Đoạn mẫu")
        self.profile_tree.heading("quality", text="Chất lượng")
        self.profile_tree.column("name", width=320)
        self.profile_tree.column("duration", width=100, anchor="center")
        self.profile_tree.column("quality", width=110, anchor="center")
        self.profile_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(library_frame, orient="vertical", command=self.profile_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.profile_tree.configure(yscrollcommand=scrollbar.set)
        actions = ttk.Frame(library_frame)
        actions.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(actions, text="Nghe thử", command=self._preview_selected).pack(side="left")
        ttk.Button(actions, text="Dừng", command=stop_audio).pack(side="left", padx=(6, 0))

        create = ttk.LabelFrame(body, text="Thêm giọng clone mới", padding=10)
        create.grid(row=2, column=0, sticky="ew")
        create.grid_columnconfigure(0, weight=1)
        ttk.Label(create, text="Tên giọng").grid(row=0, column=0, sticky="w")
        ttk.Entry(create, textvariable=self.profile_name).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(create, text="File ghi âm nguồn").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(create, textvariable=self.source_path, foreground="#667085").grid(
            row=3, column=0, sticky="ew", padx=(0, 8)
        )
        self.source_button = ttk.Button(create, text="Chọn file…", command=self._choose_source)
        self.source_button.grid(row=3, column=1)
        ttk.Label(
            create,
            text="Tự chọn đoạn nói tốt nhất 3–8 giây, lọc ù/rít, giảm nhiễu nền và chuẩn hóa âm lượng.",
            foreground="#667085",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(7, 0))
        self.process_button = ttk.Button(
            create, text="Phân tích, làm sạch và lưu giọng", command=self._start_processing
        )
        self.process_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(9, 0))
        ttk.Label(create, textvariable=self.status_text, foreground="#667085").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(7, 0)
        )
        self.progress = ttk.Progressbar(create, mode="indeterminate")
        self.progress.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(5, 0))

    def _choose_cli(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="Chọn omnivoice-infer.exe",
            filetypes=[("OmniVoice CLI", "omnivoice-infer.exe omnivoice-infer"), ("Tất cả file", "*.*")],
        )
        if selected:
            self.cli_path.set(selected)
            self._save_cli_settings()

    def _save_cli_settings(self, show_status: bool = True) -> None:
        current = VoiceSettings.load()
        value = self.cli_path.get().strip()
        VoiceSettings(cli_path=value, selected_profile_id=current.selected_profile_id).save()
        self.on_log("Đã lưu đường dẫn OmniVoice dùng chung.")
        if show_status:
            self.status_text.set("Đã lưu cấu hình OmniVoice; lần mở sau app sẽ tự nạp lại.")

    def _choose_source(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="Chọn file ghi âm giọng mẫu",
            filetypes=[("Âm thanh", "*.wav *.mp3 *.m4a *.aac *.ogg *.flac"), ("Tất cả file", "*.*")],
        )
        if selected:
            self.source_path.set(selected)

    def _refresh_profiles(self) -> None:
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        for profile in self.library.profiles:
            self.profile_tree.insert(
                "", "end", iid=profile.profile_id,
                values=(profile.name, f"{profile.duration_seconds:.1f} giây", f"{profile.quality_score}/100"),
            )

    def _preview_selected(self) -> None:
        selected = self.profile_tree.selection()
        if not selected:
            messagebox.showinfo("Chưa chọn giọng", "Hãy chọn một giọng để nghe thử.", parent=self)
            return
        profile = self.library.get(selected[0])
        if profile:
            try:
                play_audio(profile.audio_path)
            except OmniVoiceError as exc:
                messagebox.showerror("Không thể nghe thử", str(exc), parent=self)

    def _start_processing(self) -> None:
        self._save_cli_settings(show_status=False)
        source = self.source_path.get()
        if source == "Chưa chọn file ghi âm" or not self.profile_name.get().strip():
            messagebox.showwarning("Thiếu thông tin", "Hãy nhập tên giọng và chọn file ghi âm.", parent=self)
            return
        profile_name = self.profile_name.get().strip()
        self.process_button.configure(state="disabled")
        self.source_button.configure(state="disabled")
        self.progress.start(12)
        self.status_text.set("Đang phân tích chất lượng và làm sạch mẫu…")

        def worker() -> None:
            try:
                profile = prepare_voice_profile(
                    profile_name, Path(source),
                    lambda line: self.events.put(("log", line)), library=self.library,
                )
                self.events.put(("done", profile))
            except (OmniVoiceError, OSError) as exc:
                self.events.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self.on_log(str(payload))
                    self.status_text.set(str(payload))
                elif kind == "done":
                    self.progress.stop()
                    self.process_button.configure(state="normal")
                    self.source_button.configure(state="normal")
                    self._refresh_profiles()
                    self.profile_tree.selection_set(payload.profile_id)
                    current = VoiceSettings.load()
                    VoiceSettings(
                        cli_path=current.cli_path,
                        selected_profile_id=payload.profile_id,
                    ).save()
                    self.status_text.set(
                        f"Đã lưu {payload.name}: {payload.duration_seconds:.1f} giây, "
                        f"chất lượng {payload.quality_score}/100. Hãy nghe thử trước khi dùng."
                    )
                    self.profile_name.set("")
                    self.source_path.set("Chưa chọn file ghi âm")
                    self.on_library_changed()
                elif kind == "error":
                    self.progress.stop()
                    self.process_button.configure(state="normal")
                    self.source_button.configure(state="normal")
                    self.status_text.set("Xử lý thất bại.")
                    messagebox.showerror("Không thể xử lý giọng mẫu", str(payload), parent=self)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll_events)

    def _close(self) -> None:
        stop_audio()
        try:
            self._save_cli_settings(show_status=False)
        except OSError as exc:
            self.on_log(f"Không thể lưu cấu hình OmniVoice: {exc}")
        self.destroy()
