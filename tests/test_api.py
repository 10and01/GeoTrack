import unittest

from backend.app import cluster_patterns, data_quality, health, hotspots, run_job, summary
from backend.models import JobRequest


class ApiSmokeTests(unittest.TestCase):
    def test_health_and_summary(self):
        self.assertEqual(health()["status"], "ok")
        self.assertIn("trajectory_count", summary())

    def test_hotspot_and_pattern_contracts(self):
        rows = hotspots(limit=3, min_users=0)
        patterns = cluster_patterns()
        self.assertLessEqual(len(rows), 3)
        if patterns:
            self.assertIn("hourly_profile", patterns[0])
        self.assertIn("valid_points", data_quality())

    def test_job_has_status(self):
        response = run_job(JobRequest(job_type="mine", max_trajectories=1, max_points=100))
        self.assertIn(response["status"], {"queued", "running", "completed"})


if __name__ == "__main__":
    unittest.main()
