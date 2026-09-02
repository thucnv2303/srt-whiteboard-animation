import unittest

from whiteboard_app.jobs import COMPLETED, FAILED, RUNNING, WAITING
from whiteboard_app.multi_job_ui import FILTERS, job_status_label, run_button_label


class MultiJobUiTests(unittest.TestCase):
    def test_status_labels_are_vietnamese(self) -> None:
        self.assertEqual(job_status_label(WAITING), "Đang chờ")
        self.assertEqual(job_status_label(RUNNING), "Đang chạy")
        self.assertEqual(job_status_label(COMPLETED), "Hoàn tất")
        self.assertEqual(job_status_label(FAILED), "Lỗi")

    def test_run_button_counts_selected_jobs(self) -> None:
        self.assertEqual(run_button_label(0), "▶ Chạy 0 job")
        self.assertEqual(run_button_label(3), "▶ Chạy 3 job")

    def test_kpi_filters_map_to_job_states(self) -> None:
        self.assertIsNone(FILTERS["total"])
        self.assertEqual(FILTERS["running"], (RUNNING,))
        self.assertEqual(FILTERS["failed"], (FAILED,))

