import json
import tempfile
import unittest
from pathlib import Path

from jobs.full_summary import scan_dataset


class FullSummaryTests(unittest.TestCase):
    def _write_plt(self, root: Path, user: str = "001", name: str = "20080101000000.plt") -> Path:
        trajectory = root / user / "Trajectory"
        trajectory.mkdir(parents=True)
        path = trajectory / name
        header = ["Geolife trajectory", "WGS84", "Altitude is in Feet", "Reserved", "0", "0"]
        rows = [
            ["39.9", "116.3", "0", "100", "0", "2008-01-01", "00:00:00"],
            ["39.9", "116.3", "0", "-777", "0", "2008-01-01", "00:00:00"],  # duplicate
            ["95", "116.3", "0", "100", "0", "2008-01-01", "00:01:00"],  # invalid latitude
            ["39.901", "116.301", "0", "100", "0", "2008-01-01", "00:02:00"],
            ["39.902", "116.302", "0", "100", "0", "2008-01-01", "01:00:00"],  # time gap
        ]
        path.write_text("\n".join(header + [",".join(row) for row in rows]), encoding="utf-8")
        return path

    def test_scan_is_bounded_and_applies_quality_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_plt(root)
            manifest = scan_dataset(root)
            self.assertEqual(manifest["counts"]["user_count"], 1)
            self.assertEqual(manifest["counts"]["plt_file_count"], 1)
            self.assertEqual(manifest["counts"]["valid_point_count"], 3)
            self.assertEqual(manifest["counts"]["invalid_point_count"], 1)
            self.assertEqual(manifest["counts"]["duplicate_point_count"], 1)
            self.assertEqual(manifest["counts"]["time_gap_segment_count"], 1)
            self.assertNotIn("points", manifest)
            self.assertEqual(manifest["files"][0]["trajectory_id"], "001_20080101000000")

    def test_manifest_round_trip_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_plt(root)
            manifest = scan_dataset(root)
            encoded = json.dumps(manifest, ensure_ascii=False)
            self.assertIn("local-full-scan", encoded)


if __name__ == "__main__":
    unittest.main()
