from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class ProjectError(ValueError):
    """Lỗi gói dự án có thể hiển thị trực tiếp cho người dùng."""


@dataclass(frozen=True)
class Scene:
    scene_id: str
    title: str
    image: Path
    annotation: Path
    duration_ms: int = 0


@dataclass
class VideoProject:
    root: Path
    manifest_path: Path
    title: str
    version: int
    scenes: list[Scene]
    script_path: Path | None = None
    script_text: str = ""
    voice: Path | None = None
    pen_brand: str | None = None
    temporary_root: Path | None = None

    def close(self) -> None:
        if self.temporary_root and self.temporary_root.exists():
            shutil.rmtree(self.temporary_root, ignore_errors=True)
            self.temporary_root = None


def _safe_relative_path(root: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ProjectError(f"{label} phải là đường dẫn không rỗng.")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ProjectError(f"{label} phải là đường dẫn tương đối: {raw}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectError(f"{label} đi ra ngoài thư mục dự án: {raw}") from exc
    return resolved


def _read_manifest(manifest_path: Path, temporary_root: Path | None = None) -> VideoProject:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ProjectError(f"Không tìm thấy project.json tại {manifest_path.parent}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectError(f"project.json không phải JSON UTF-8 hợp lệ: {exc}") from exc

    if not isinstance(data, dict):
        raise ProjectError("Nội dung project.json phải là một object JSON.")
    schema_version = data.get("schemaVersion", 1)
    if schema_version != 1:
        raise ProjectError(f"Chưa hỗ trợ schemaVersion={schema_version}; phiên bản hiện tại là 1.")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ProjectError("project.json thiếu title.")
    version = data.get("version", 1)
    if not isinstance(version, int) or version < 1:
        raise ProjectError("version phải là số nguyên lớn hơn hoặc bằng 1.")

    root = manifest_path.parent.resolve()
    raw_scenes = data.get("scenes")
    if not isinstance(raw_scenes, list) or not raw_scenes:
        raise ProjectError("project.json phải có ít nhất một scene.")

    scenes: list[Scene] = []
    seen_ids: set[str] = set()
    for index, raw_scene in enumerate(raw_scenes, start=1):
        if not isinstance(raw_scene, dict):
            raise ProjectError(f"Scene {index} phải là object JSON.")
        scene_id = raw_scene.get("id")
        if not isinstance(scene_id, str) or not scene_id.strip():
            raise ProjectError(f"Scene {index} thiếu id.")
        if scene_id in seen_ids:
            raise ProjectError(f"Scene id bị trùng: {scene_id}")
        seen_ids.add(scene_id)

        image = _safe_relative_path(root, raw_scene.get("image"), f"Ảnh của {scene_id}")
        annotation = _safe_relative_path(
            root, raw_scene.get("annotation"), f"Annotation của {scene_id}"
        )
        if not image.is_file():
            raise ProjectError(f"Không tìm thấy ảnh của {scene_id}: {image}")
        if not annotation.is_file():
            raise ProjectError(f"Không tìm thấy annotation của {scene_id}: {annotation}")
        if image.stem != annotation.name.removesuffix(".annotation.json"):
            raise ProjectError(
                f"Ảnh và annotation của {scene_id} phải cùng tên: "
                f"{image.name} / {annotation.name}"
            )
        duration_ms = 0
        try:
            annotation_data = json.loads(annotation.read_text(encoding="utf-8-sig"))
            raw_duration = annotation_data.get("sceneDurationMs", 0)
            if isinstance(raw_duration, int) and raw_duration > 0:
                duration_ms = raw_duration
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
            pass
        scenes.append(
            Scene(
                scene_id=scene_id,
                title=str(raw_scene.get("title") or scene_id),
                image=image,
                annotation=annotation,
                duration_ms=duration_ms,
            )
        )

    script_path: Path | None = None
    script_text = ""
    raw_script = data.get("script")
    if raw_script is not None:
        script_path = _safe_relative_path(root, raw_script, "Kịch bản")
        if not script_path.is_file():
            raise ProjectError(f"Không tìm thấy kịch bản: {script_path}")
    else:
        conventional_script = root / "script.txt"
        if conventional_script.is_file():
            script_path = conventional_script
    if script_path:
        try:
            script_text = script_path.read_text(encoding="utf-8-sig").strip()
        except (OSError, UnicodeError) as exc:
            raise ProjectError(f"Không thể đọc kịch bản UTF-8: {script_path}") from exc
        if not script_text:
            raise ProjectError("Kịch bản không được để trống.")

    voice: Path | None = None
    if data.get("voice") is not None:
        voice = _safe_relative_path(root, data["voice"], "Voice")
        if not voice.is_file():
            raise ProjectError(f"Không tìm thấy voice: {voice}")

    pen_brand: str | None = None
    if data.get("penBrand") is not None:
        raw_pen_brand = data["penBrand"]
        if not isinstance(raw_pen_brand, str) or not raw_pen_brand.strip():
            raise ProjectError("penBrand phải là chuỗi không rỗng.")
        pen_brand = raw_pen_brand.strip()
        if len(pen_brand) > 40:
            raise ProjectError("penBrand không được dài quá 40 ký tự.")

    return VideoProject(
        root=root,
        manifest_path=manifest_path.resolve(),
        title=title.strip(),
        version=version,
        scenes=scenes,
        script_path=script_path,
        script_text=script_text,
        voice=voice,
        pen_brand=pen_brand,
        temporary_root=temporary_root,
    )


def _extract_zip(source: Path) -> tuple[Path, Path]:
    temporary_root = Path(tempfile.mkdtemp(prefix="whiteboard-project-"))
    try:
        with zipfile.ZipFile(source) as archive:
            members = archive.infolist()
            if not members:
                raise ProjectError("File ZIP rỗng.")
            for member in members:
                posix_path = PurePosixPath(member.filename)
                if posix_path.is_absolute() or ".." in posix_path.parts:
                    raise ProjectError(f"ZIP chứa đường dẫn không an toàn: {member.filename}")
                destination = (temporary_root / Path(*posix_path.parts)).resolve()
                try:
                    destination.relative_to(temporary_root.resolve())
                except ValueError as exc:
                    raise ProjectError(
                        f"ZIP chứa đường dẫn không an toàn: {member.filename}"
                    ) from exc
            archive.extractall(temporary_root)
    except (OSError, zipfile.BadZipFile) as exc:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise ProjectError(f"Không thể mở file ZIP: {exc}") from exc

    manifests = list(temporary_root.rglob("project.json"))
    if len(manifests) != 1:
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise ProjectError("ZIP phải chứa đúng một file project.json.")
    return manifests[0], temporary_root


def load_project(source: str | Path) -> VideoProject:
    path = Path(source).expanduser().resolve()
    if path.is_dir():
        return _read_manifest(path / "project.json")
    if path.is_file() and path.suffix.lower() == ".zip":
        manifest, temporary_root = _extract_zip(path)
        try:
            return _read_manifest(manifest, temporary_root)
        except Exception:
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise
    if path.is_file() and path.name.lower() == "project.json":
        return _read_manifest(path)
    raise ProjectError("Hãy chọn thư mục dự án, project.json hoặc file ZIP.")
