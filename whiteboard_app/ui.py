from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .project import ProjectError, VideoProject, load_project
from .renderer import RenderError, run_pipeline


class WhiteboardApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Tạo video vẽ tay")
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.project: VideoProject | None = None
        self.output_dir: Path | None = None
        self.cancel_event = threading.Event()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_styles()
        self._build_ui()
        self.after(100, self._poll_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#5f6368")
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"), foreground="#1b6b42")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(18, 10))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Tạo video vẽ tay", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Nhập gói dự án từ ChatGPT, kiểm tra cảnh và dựng video MP4 trên máy.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 18))

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(0, 14))
        self.open_button = ttk.Button(toolbar, text="Mở thư mục / ZIP", command=self._choose_project)
        self.open_button.pack(side="left")
        self.output_button = ttk.Button(toolbar, text="Chọn nơi xuất", command=self._choose_output)
        self.output_button.pack(side="left", padx=8)
        self.render_button = ttk.Button(
            toolbar, text="Tạo video", style="Accent.TButton", command=self._start_render, state="disabled"
        )
        self.render_button.pack(side="right")
        self.cancel_button = ttk.Button(toolbar, text="Hủy", command=self.cancel_event.set, state="disabled")
        self.cancel_button.pack(side="right", padx=8)

        info = ttk.LabelFrame(outer, text="Dự án", padding=12)
        info.pack(fill="x", pady=(0, 12))
        self.project_label = ttk.Label(info, text="Chưa mở dự án")
        self.project_label.pack(anchor="w")
        self.path_label = ttk.Label(info, text="", style="Subtitle.TLabel")
        self.path_label.pack(anchor="w", pady=(4, 0))
        self.status_label = ttk.Label(info, text="Sẵn sàng", style="Status.TLabel")
        self.status_label.pack(anchor="e")

        body = ttk.Panedwindow(outer, orient="horizontal")
        body.pack(fill="both", expand=True)
        scene_frame = ttk.LabelFrame(body, text="Danh sách cảnh", padding=8)
        log_frame = ttk.LabelFrame(body, text="Nhật ký dựng", padding=8)
        body.add(scene_frame, weight=2)
        body.add(log_frame, weight=3)

        self.scene_tree = ttk.Treeview(
            scene_frame, columns=("title", "image", "state"), show="headings", height=14
        )
        self.scene_tree.heading("title", text="Cảnh")
        self.scene_tree.heading("image", text="Ảnh")
        self.scene_tree.heading("state", text="Trạng thái")
        self.scene_tree.column("title", width=170)
        self.scene_tree.column("image", width=200)
        self.scene_tree.column("state", width=90, anchor="center")
        self.scene_tree.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=18,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
            background="#17202a",
            foreground="#e8edf2",
            insertbackground="white",
        )
        self.log_text.pack(fill="both", expand=True)

    def _choose_project(self) -> None:
        source = filedialog.askopenfilename(
            title="Chọn project.json hoặc gói ZIP",
            filetypes=[("Dự án video", "project.json *.zip"), ("Tất cả file", "*.*")],
        )
        if not source:
            folder = filedialog.askdirectory(title="Hoặc chọn thư mục có project.json")
            source = folder
        if not source:
            return
        try:
            loaded = load_project(source)
        except ProjectError as exc:
            messagebox.showerror("Không thể mở dự án", str(exc), parent=self)
            return
        if self.project:
            self.project.close()
        self.project = loaded
        self.output_dir = loaded.root / "output" if loaded.temporary_root is None else None
        self.project_label.configure(
            text=f"{loaded.title}  •  phiên bản {loaded.version}  •  {len(loaded.scenes)} cảnh"
        )
        self.path_label.configure(text=str(loaded.manifest_path))
        for item in self.scene_tree.get_children():
            self.scene_tree.delete(item)
        for scene in loaded.scenes:
            self.scene_tree.insert("", "end", iid=scene.scene_id, values=(scene.title, scene.image.name, "Hợp lệ"))
        self._append_log(f"Đã mở dự án: {loaded.title}")
        if loaded.voice:
            self._append_log(f"Voice: {loaded.voice.name}")
        self.render_button.configure(state="normal")
        self.status_label.configure(text="Dự án hợp lệ")

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory(title="Chọn thư mục xuất video")
        if selected:
            self.output_dir = Path(selected)
            self._append_log(f"Thư mục xuất: {self.output_dir}")

    def _start_render(self) -> None:
        if not self.project:
            return
        if self.output_dir is None:
            self._choose_output()
        if self.output_dir is None:
            return
        final = self.output_dir / "final.mp4"
        if final.exists() and not messagebox.askyesno(
            "Ghi đè video", f"{final} đã tồn tại. Bạn có muốn ghi đè?", parent=self
        ):
            return
        self.cancel_event.clear()
        self._set_busy(True)
        project = self.project
        output_dir = self.output_dir

        def worker() -> None:
            try:
                result = run_pipeline(
                    project,
                    output_dir,
                    lambda line: self.events.put(("log", line)),
                    self.cancel_event,
                )
                self.events.put(("done", result))
            except (RenderError, OSError) as exc:
                self.events.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.open_button.configure(state=state)
        self.output_button.configure(state=state)
        self.render_button.configure(state=state if self.project else "disabled")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        self.status_label.configure(text="Đang dựng video…" if busy else "Sẵn sàng")

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
                elif kind == "done":
                    self._set_busy(False)
                    self.status_label.configure(text="Đã tạo video")
                    self._append_log(f"Hoàn tất: {payload}")
                    messagebox.showinfo("Hoàn tất", f"Video đã được tạo tại:\n{payload}", parent=self)
                elif kind == "error":
                    self._set_busy(False)
                    self.status_label.configure(text="Có lỗi")
                    self._append_log(f"LỖI: {payload}")
                    messagebox.showerror("Dựng video thất bại", str(payload), parent=self)
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

