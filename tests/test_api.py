import unittest
import tempfile
import time
from pathlib import Path

from backend.app import cluster_patterns, data_quality, health, hotspots, run_job, summary
from backend.models import JobRequest
import backend.store as store_module


class ApiSmokeTests(unittest.TestCase):
    def test_health_and_summary(self):
        health_payload = health()
        self.assertEqual(health_payload["status"], "ok")
        self.assertIn("full_index_available", health_payload)
        self.assertIn("trajectory_count", summary())

    def test_hotspot_and_pattern_contracts(self):
        rows = hotspots(limit=3, min_users=0)
        patterns = cluster_patterns()
        self.assertLessEqual(len(rows), 3)
        if patterns:
            self.assertIn("hourly_profile", patterns[0])
        self.assertIn("valid_points", data_quality())

    def test_trajectory_list_is_summary_only_and_detail_has_points(self):
        rows = __import__("backend.app", fromlist=["trajectories"]).trajectories(limit=1)
        self.assertLessEqual(len(rows), 1)
        if rows:
            self.assertNotIn("points", rows[0])
            detail = __import__("backend.app", fromlist=["trajectory"]).trajectory(rows[0]["trajectory_id"])
            self.assertIsNotNone(detail)
            self.assertIn("points", detail)
    def test_job_has_status(self):
        # Keep the asynchronous smoke test isolated from the serving snapshot
        # used by the rest of the suite and by the acceptance runner.
        with tempfile.TemporaryDirectory() as temp:
            original_data_file = store_module.DATA_FILE
            store_module.DATA_FILE = Path(temp) / "demo.json"
            try:
                response = run_job(JobRequest(job_type="mine", max_trajectories=1, max_points=100))
                self.assertIn(response["status"], {"queued", "running", "completed"})
                deadline = time.monotonic() + 10
                status = response
                while status["status"] in {"queued", "running"} and time.monotonic() < deadline:
                    time.sleep(0.02)
                    status = store_module.store.job(response["job_id"]) or status
                self.assertEqual(status["status"], "completed")
            finally:
                store_module.DATA_FILE = original_data_file
                store_module.store.reload()


if __name__ == "__main__":
    unittest.main()
