import json
import tempfile
import unittest
from pathlib import Path

from jobs.check_serving_payload import counts
from jobs.load_serving_tables import load


class ServingPayloadTests(unittest.TestCase):
    def test_dry_run_counts_persisted_stay_points(self):
        payload = {
            "trajectories": [{"trajectory_id": "t", "points": [{"timestamp": "2024-01-01T00:00:00Z"}]}],
            "stay_points": [{"stay_id": "s", "trajectory_id": "t"}],
            "hotspots": [],
            "patterns": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            expected = {"trajectory_points": 1, "trajectories": 1, "stay_points": 1, "hotspots": 0, "temporal_patterns": 0}
            self.assertEqual(counts(path), expected)
            self.assertEqual(load(path, "unused", dry_run=True), expected)


if __name__ == "__main__":
    unittest.main()
