from __future__ import annotations

import json
import shutil
import subprocess
import wave
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .project import NarrationCue, VideoProject


class TimelineError(RuntimeError):
    """Lỗi biên dịch timeline có thể hiển thị trực tiếp trên UI."""


@dataclass(frozen=True)
class CueTiming:
    cue_id: str
    scene_id: str
    text: str
    element_ids: list[str]
    start_ms: int
    duration_ms: int
    end_ms: int


@dataclass(frozen=True)
class TimelineResult:
    voice_path: Path
    timeline_path: Path
    runtime_annotations: dict[str, Path]
    cues: list[CueTiming]
    total_duration_ms: int


def wav_duration_ms(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as audio:
            return round(audio.getnframes() * 1000 / audio.getframerate())
    except (OSError, wave.Error, ZeroDivisionError) as exc:
        raise TimelineError(f"Không đọc được thời lượng WAV: {path}") from exc


def _schedule_elements(
    annotation: dict[str, object],
    cue: NarrationCue,
    cue_start_ms: int,
    cue_duration_ms: int,
) -> set[str]:
    scheduled: set[str] = set()
    if not cue.element_ids:
        return scheduled
    elements = annotation.get("elements", [])
    if not isinstance(elements, list):
        raise TimelineError(f"Annotation của {cue.scene_id} thiếu elements.")
    element_lookup = {
        str(element.get("id")): element
        for element in elements
        if isinstance(element, dict) and isinstance(element.get("id"), str)
    }
    draw_start = cue_start_ms + 100
    draw_budget = max(900, cue_duration_ms - 500)
    each_duration = max(600, draw_budget // len(cue.element_ids))
    for index, element_id in enumerate(cue.element_ids):
        element = element_lookup.get(element_id)
        if element is None:
            raise TimelineError(f"Cue {cue.cue_id} không tìm thấy element {element_id}.")
        reveal = element.setdefault("reveal", {})
        if not isinstance(reveal, dict):
            raise TimelineError(f"Element {element_id} có reveal không hợp lệ.")
        reveal["startMs"] = draw_start + index * each_duration
        reveal["durationMs"] = each_duration
        scheduled.add(element_id)
    return scheduled


def compile_timeline(
    project: VideoProject,
    cue_audio: dict[str, Path],
    output_dir: Path,
    on_log: Callable[[str], None],
) -> TimelineResult:
    if not project.narration_cues:
        raise TimelineError("Dự án chưa có narration cue.")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise TimelineError("Cần FFmpeg trong PATH để ghép audio timeline.")

    output_dir = output_dir.resolve()
    annotation_dir = output_dir / "runtime-annotations"
    annotation_dir.mkdir(parents=True, exist_ok=True)
    scene_cues: dict[str, list[NarrationCue]] = {scene.scene_id: [] for scene in project.scenes}
    for cue in project.narration_cues:
        scene_cues[cue.scene_id].append(cue)

    runtime_annotations: dict[str, Path] = {}
    timings: list[CueTiming] = []
    scene_rows: list[dict[str, object]] = []
    global_cursor = 0
    used_elements: dict[str, set[str]] = {scene.scene_id: set() for scene in project.scenes}

    for scene in project.scenes:
        try:
            source_annotation = json.loads(scene.annotation.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise TimelineError(f"Không đọc được annotation của {scene.scene_id}: {exc}") from exc
        annotation = deepcopy(source_annotation)
        local_cursor = 0
        local_cues: list[dict[str, object]] = []
        for cue in scene_cues[scene.scene_id]:
            audio_path = cue_audio.get(cue.cue_id)
            if not audio_path or not audio_path.is_file():
                raise TimelineError(f"Thiếu audio cho cue {cue.cue_id}.")
            duration_ms = wav_duration_ms(audio_path)
            local_cursor += cue.pause_before_ms
            local_start = local_cursor
            global_start = global_cursor + local_start
            duplicated = used_elements[scene.scene_id].intersection(cue.element_ids)
            if duplicated:
                raise TimelineError(
                    f"Element đã được gán cho nhiều cue: {', '.join(sorted(duplicated))}"
                )
            used_elements[scene.scene_id].update(
                _schedule_elements(annotation, cue, local_start, duration_ms)
            )
            timing = CueTiming(
                cue_id=cue.cue_id,
                scene_id=scene.scene_id,
                text=cue.text,
                element_ids=cue.element_ids,
                start_ms=global_start,
                duration_ms=duration_ms,
                end_ms=global_start + duration_ms,
            )
            timings.append(timing)
            local_cues.append(
                {
                    "id": cue.cue_id,
                    "text": cue.text,
                    "elementIds": cue.element_ids,
                    "localStartMs": local_start,
                    "globalStartMs": global_start,
                    "durationMs": duration_ms,
                    "audio": str(audio_path),
                }
            )
            local_cursor = local_start + duration_ms + cue.pause_after_ms

        if local_cues:
            scene_duration = local_cursor + 500
            annotation["sceneDurationMs"] = scene_duration
        else:
            scene_duration = int(annotation.get("sceneDurationMs", scene.duration_ms or 1000))
        runtime_path = annotation_dir / f"{scene.scene_id}.annotation.json"
        runtime_path.write_text(
            json.dumps(annotation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        runtime_annotations[scene.scene_id] = runtime_path
        all_elements = {
            str(element.get("id"))
            for element in annotation.get("elements", [])
            if isinstance(element, dict) and isinstance(element.get("id"), str)
        }
        unmapped = sorted(all_elements - used_elements[scene.scene_id])
        if unmapped and local_cues:
            on_log(f"CẢNH BÁO {scene.scene_id}: element chưa gắn cue: {', '.join(unmapped)}")
        scene_rows.append(
            {
                "sceneId": scene.scene_id,
                "globalStartMs": global_cursor,
                "durationMs": scene_duration,
                "runtimeAnnotation": str(runtime_path),
                "cues": local_cues,
            }
        )
        global_cursor += scene_duration

    total_duration_ms = global_cursor
    audio_inputs: list[str] = []
    filters: list[str] = []
    delayed_labels: list[str] = []
    for index, timing in enumerate(timings):
        audio_inputs.extend(["-i", str(cue_audio[timing.cue_id])])
        label = f"a{index}"
        filters.append(f"[{index}:a]adelay={timing.start_ms}:all=1[{label}]")
        delayed_labels.append(f"[{label}]")
    if not delayed_labels:
        raise TimelineError("Timeline không có cue audio.")
    if len(delayed_labels) == 1:
        mixed = f"{delayed_labels[0]}apad=pad_dur=5,atrim=duration={total_duration_ms / 1000:.3f}[out]"
    else:
        mixed = (
            "".join(delayed_labels)
            + f"amix=inputs={len(delayed_labels)}:duration=longest:normalize=0,"
            + f"apad=pad_dur=5,atrim=duration={total_duration_ms / 1000:.3f}[out]"
        )
    filters.append(mixed)
    voice_path = output_dir / "voice-timeline.wav"
    command = [
        ffmpeg, "-y", "-loglevel", "error", *audio_inputs,
        "-filter_complex", ";".join(filters), "-map", "[out]",
        "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(voice_path),
    ]
    on_log("Đang ghép các cue voice theo timeline…")
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 or not voice_path.is_file():
        raise TimelineError(f"Ghép voice timeline thất bại: {result.stderr.strip()}")

    timeline_path = output_dir / "timeline.json"
    timeline_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "audioIsClock": True,
                "totalDurationMs": total_duration_ms,
                "voice": str(voice_path),
                "scenes": scene_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    on_log(f"Đã đồng bộ {len(timings)} cue — tổng {total_duration_ms / 1000:.1f} giây.")
    return TimelineResult(
        voice_path=voice_path,
        timeline_path=timeline_path,
        runtime_annotations=runtime_annotations,
        cues=timings,
        total_duration_ms=total_duration_ms,
    )
