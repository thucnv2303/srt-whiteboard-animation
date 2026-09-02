import unittest
from pathlib import Path
from unittest.mock import Mock

from whiteboard_app.jobs import CANCELED, COMPLETED, FAILED, QUEUED, RUNNING, WAITING
from whiteboard_app.multi_job_ui import (
    FILTERS,
    bulk_output_directory,
    header_checkbox_text,
    job_settings_editable,
    job_settings_rows,
    job_status_label,
    multi_job_layout,
    run_button_label,
    settings_button_label,
    settings_target_ids,
)


class MultiJobUiTests(unittest.TestCase):
    def test_status_labels_are_vietnamese(self) -> None:
        self.assertEqual(job_status_label(WAITING), "Đang chờ")
        self.assertEqual(job_status_label(RUNNING), "Đang chạy")
        self.assertEqual(job_status_label(COMPLETED), "Hoàn tất")
        self.assertEqual(job_status_label(FAILED), "Lỗi")

    def test_run_button_counts_selected_jobs(self) -> None:
        self.assertEqual(run_button_label(0), "▶ Chạy 0 job")
        self.assertEqual(run_button_label(3), "▶ Chạy 3 job")

    def test_settings_button_counts_checked_jobs(self) -> None:
        self.assertEqual(settings_button_label(1, False), "⚙ Thiết lập job")
        self.assertEqual(settings_button_label(5, True), "⚙ Thiết lập 5 job")

    def test_kpi_filters_map_to_job_states(self) -> None:
        self.assertIsNone(FILTERS["total"])
        self.assertEqual(FILTERS["running"], (RUNNING,))
        self.assertEqual(FILTERS["failed"], (FAILED,))

    def test_popup_rows_show_the_job_snapshot(self) -> None:
        job = Mock(
            voice_name="Xuân Dung",
            aspect_ratio="9:16",
            pen_brand="Ăn dặm mẹ Dâu",
            output_dir=Path(r"E:\Project AI\output\runs\job-01"),
        )
        rows = dict(job_settings_rows(job))
        self.assertEqual(rows["Giọng đọc"], "Xuân Dung")
        self.assertEqual(rows["Khung hình"], "9:16")
        self.assertIn("job-01", rows["Nơi lưu"])

    def test_only_unstarted_or_retryable_jobs_have_editable_settings(self) -> None:
        self.assertTrue(job_settings_editable(WAITING))
        self.assertTrue(job_settings_editable(FAILED))
        self.assertTrue(job_settings_editable(CANCELED))
        self.assertTrue(job_settings_editable(COMPLETED))
        self.assertFalse(job_settings_editable(QUEUED))
        self.assertFalse(job_settings_editable(RUNNING))

    def test_header_checkbox_reflects_all_visible_jobs(self) -> None:
        visible = ["job-1", "job-2", "job-3"]
        self.assertEqual(header_checkbox_text(visible, set()), "☐")
        self.assertEqual(header_checkbox_text(visible, {"job-1"}), "▣")
        self.assertEqual(header_checkbox_text(visible, set(visible)), "☑")

    def test_settings_apply_to_every_checked_job(self) -> None:
        jobs = [Mock(job_id=f"job-{index}") for index in range(1, 6)]
        checked = {job.job_id for job in jobs}
        self.assertEqual(
            settings_target_ids(jobs, checked, "job-1"),
            ["job-1", "job-2", "job-3", "job-4", "job-5"],
        )
        self.assertEqual(settings_target_ids(jobs, set(), "job-3"), ["job-3"])

    def test_bulk_output_keeps_each_job_in_a_separate_folder(self) -> None:
        root = Path("output") / "runs"
        first = bulk_output_directory(root, "job-1")
        second = bulk_output_directory(root, "job-2")
        self.assertNotEqual(first, second)
        self.assertEqual(first.name, "job-1")
        self.assertEqual(second.name, "job-2")

    def test_multi_job_layout_uses_three_columns_on_desktop(self) -> None:
        self.assertEqual(multi_job_layout(1280), "three")
        self.assertEqual(multi_job_layout(1000), "two")
        self.assertEqual(multi_job_layout(760), "stack")
