import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from whiteboard_app.jobs import (
    CANCELED,
    COMPLETED,
    FAILED,
    QUEUED,
    RUNNING,
    WAITING,
    JobResult,
    JobStore,
    SequentialJobRunner,
)
from whiteboard_app.project import load_project


def make_project(root: Path, title: str = "Job mẫu") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "scene.png").write_bytes(b"png")
    (root / "scene.annotation.json").write_text(
        json.dumps({"sceneDurationMs": 1200, "elements": []}), encoding="utf-8"
    )
    manifest = root / "project.json"
    manifest.write_text(
        json.dumps(
            {
                "title": title,
                "scenes": [
                    {
                        "id": "scene-01",
                        "image": "scene.png",
                        "annotation": "scene.annotation.json",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest


class JobStoreTests(unittest.TestCase):
    def test_add_snapshots_project_settings_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root / "project", "Bữa sáng cho bé")
            project = load_project(manifest)
            store = JobStore(root / "jobs.db")
            job = store.add(
                manifest,
                project,
                aspect_ratio="9:16",
                pen_brand="Ăn dặm mẹ Dâu",
                voice_profile_id="voice-1",
                voice_name="Xuân Dung",
                voice_audio_path=root / "voice.wav",
                cli_path="omnivoice-infer.exe",
                output_dir=root / "runs" / "job-1",
            )
            self.assertEqual(job.status, WAITING)
            self.assertEqual(job.aspect_ratio, "9:16")
            self.assertEqual(job.voice_name, "Xuân Dung")
            self.assertEqual(job.duration_seconds, 1.2)
            self.assertEqual(store.counts()["waiting"], 1)
            self.assertIn("Đã thêm dự án", store.logs(job.job_id)[0][1])

    def test_queue_failed_retry_and_recover_interrupted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root / "project")
            project = load_project(manifest)
            store = JobStore(root / "jobs.db")
            job = store.add(manifest, project, "16:9", "", "", "", None, "", root / "run")
            self.assertEqual(store.queue([job.job_id]), 1)
            self.assertEqual(store.get(job.job_id).status, QUEUED)  # type: ignore[union-attr]
            store.mark_running(job.job_id)
            self.assertEqual(store.get(job.job_id).status, RUNNING)  # type: ignore[union-attr]
            self.assertEqual(store.recover_interrupted(), 1)
            self.assertEqual(store.get(job.job_id).status, FAILED)  # type: ignore[union-attr]
            self.assertTrue(store.retry(job.job_id))
            self.assertEqual(store.get(job.job_id).status, WAITING)  # type: ignore[union-attr]

    def test_queued_job_from_previous_session_waits_for_a_new_start_click(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root / "project")
            project = load_project(manifest)
            store = JobStore(root / "jobs.db")
            job = store.add(manifest, project, "16:9", "", "", "", None, "", root / "run")
            self.assertEqual(store.queue([job.job_id]), 1)

            self.assertEqual(store.recover_interrupted(), 1)
            recovered = store.get(job.job_id)
            self.assertEqual(recovered.status, WAITING)  # type: ignore[union-attr]
            self.assertEqual(recovered.phase, "")  # type: ignore[union-attr]

    def test_updates_waiting_job_settings_but_not_running_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root / "project")
            project = load_project(manifest)
            store = JobStore(root / "jobs.db")
            job = store.add(manifest, project, "16:9", "Cũ", "voice-1", "Giọng cũ", root / "old.wav", "old.exe", root / "old-run")

            self.assertTrue(
                store.update_settings(
                    job.job_id,
                    aspect_ratio="9:16",
                    pen_brand="Thương hiệu mới",
                    voice_profile_id="voice-2",
                    voice_name="Giọng mới",
                    voice_audio_path=root / "new.wav",
                    cli_path="new.exe",
                    output_dir=root / "new-run",
                )
            )
            updated = store.get(job.job_id)
            self.assertEqual(updated.aspect_ratio, "9:16")  # type: ignore[union-attr]
            self.assertEqual(updated.voice_name, "Giọng mới")  # type: ignore[union-attr]
            self.assertEqual(updated.output_dir, root / "new-run")  # type: ignore[union-attr]
            reopened = JobStore(root / "jobs.db").get(job.job_id)
            self.assertEqual(reopened.aspect_ratio, "9:16")  # type: ignore[union-attr]
            self.assertEqual(reopened.pen_brand, "Thương hiệu mới")  # type: ignore[union-attr]
            self.assertEqual(reopened.voice_name, "Giọng mới")  # type: ignore[union-attr]
            self.assertEqual(reopened.output_dir, root / "new-run")  # type: ignore[union-attr]
            store.mark_running(job.job_id)
            self.assertFalse(
                store.update_settings(
                    job.job_id,
                    aspect_ratio="1:1",
                    pen_brand="Không được lưu",
                    voice_profile_id="",
                    voice_name="",
                    voice_audio_path=None,
                    cli_path="",
                    output_dir=root / "blocked",
                )
            )
            self.assertEqual(store.get(job.job_id).aspect_ratio, "9:16")  # type: ignore[union-attr]

    def test_editing_completed_job_resets_it_for_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = make_project(root / "project")
            project = load_project(manifest)
            store = JobStore(root / "jobs.db")
            job = store.add(manifest, project, "16:9", "", "", "", None, "", root / "run")
            result = root / "run" / "final.mp4"
            result.parent.mkdir(parents=True)
            result.write_bytes(b"mp4")
            store.mark_completed(job.job_id, JobResult(result, None, None, 1.2))

            self.assertTrue(
                store.update_settings(
                    job.job_id,
                    aspect_ratio="1:1",
                    pen_brand="Chạy lại",
                    voice_profile_id="",
                    voice_name="",
                    voice_audio_path=None,
                    cli_path="",
                    output_dir=root / "rerun",
                )
            )
            updated = store.get(job.job_id)
            self.assertEqual(updated.status, WAITING)  # type: ignore[union-attr]
            self.assertEqual(updated.progress, 0)  # type: ignore[union-attr]
            self.assertIsNone(updated.result_path)  # type: ignore[union-attr]


class SequentialRunnerTests(unittest.TestCase):
    def test_cancel_waiting_job_without_starting_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = JobStore(root / "jobs.db")
            manifest = make_project(root / "cancel-project")
            project = load_project(manifest)
            job = store.add(manifest, project, "16:9", "", "", "", None, "", root / "cancel-run")
            runner = SequentialJobRunner(store)
            try:
                self.assertTrue(runner.cancel(job.job_id))
                self.assertEqual(store.get(job.job_id).status, CANCELED)  # type: ignore[union-attr]
            finally:
                runner.stop()

    def test_runs_queued_jobs_in_order_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = JobStore(root / "jobs.db")
            jobs = []
            for index in range(2):
                manifest = make_project(root / f"project-{index}", f"Job {index}")
                project = load_project(manifest)
                jobs.append(
                    store.add(
                        manifest, project, "16:9", "", "", "", None, "", root / f"run-{index}"
                    )
                )
            completed = threading.Event()
            order: list[str] = []

            def executor(job, _cancel, progress, log):
                order.append(job.job_id)
                progress("Đang dựng", 50)
                log("fixture")
                result = job.output_dir / "final.mp4"
                result.parent.mkdir(parents=True, exist_ok=True)
                result.write_bytes(b"mp4")
                return JobResult(result, None, None, 1.2)

            def event(kind: str, _job_id: str, _payload: object) -> None:
                if kind == "completed" and len(order) == 2:
                    completed.set()

            runner = SequentialJobRunner(store, on_event=event, executor=executor)
            try:
                self.assertEqual(runner.queue([job.job_id for job in jobs]), 2)
                self.assertTrue(completed.wait(3))
                deadline = time.monotonic() + 2
                while any(store.get(job.job_id).status != COMPLETED for job in jobs):  # type: ignore[union-attr]
                    if time.monotonic() >= deadline:
                        self.fail("Runner chưa ghi trạng thái hoàn tất")
                    time.sleep(0.01)
                self.assertEqual(order, [job.job_id for job in jobs])
            finally:
                runner.stop()

    def test_failed_job_does_not_block_the_next_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = JobStore(root / "jobs.db")
            jobs = []
            for index in range(2):
                manifest = make_project(root / f"failure-project-{index}", f"Job {index}")
                project = load_project(manifest)
                jobs.append(
                    store.add(
                        manifest, project, "16:9", "", "", "", None, "", root / f"failure-run-{index}"
                    )
                )
            second_done = threading.Event()

            def executor(job, _cancel, _progress, _log):
                if job.job_id == jobs[0].job_id:
                    raise OSError("fixture lỗi")
                result = job.output_dir / "final.mp4"
                result.parent.mkdir(parents=True, exist_ok=True)
                result.write_bytes(b"mp4")
                return JobResult(result, None, None, 1.2)

            def event(kind: str, job_id: str, _payload: object) -> None:
                if kind == "completed" and job_id == jobs[1].job_id:
                    second_done.set()

            runner = SequentialJobRunner(store, on_event=event, executor=executor)
            try:
                runner.queue([job.job_id for job in jobs])
                self.assertTrue(second_done.wait(3))
                self.assertEqual(store.get(jobs[0].job_id).status, FAILED)  # type: ignore[union-attr]
                self.assertEqual(store.get(jobs[1].job_id).status, COMPLETED)  # type: ignore[union-attr]
            finally:
                runner.stop()


if __name__ == "__main__":
    unittest.main()
