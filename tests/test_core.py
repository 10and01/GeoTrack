import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jobs.geotrack_core import build_hotspots, extract_stay_points, haversine_m, trajectory_from_points, write_dataset


class CoreAlgorithmTests(unittest.TestCase):
    def test_haversine_known_distance(self):
        self.assertAlmostEqual(haversine_m(0, 0, 0, 1), 111_195, delta=300)

    def test_stay_point_requires_duration(self):
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        points = [
            {"timestamp": start + timedelta(minutes=i * 5), "latitude": 39.9 + i * 0.00001, "longitude": 116.3 + i * 0.00001, "user_id": "u", "trajectory_id": "t"}
            for i in range(6)
        ]
        stays = extract_stay_points(points, radius_m=200, min_duration_s=20 * 60)
        self.assertEqual(len(stays), 1)
        self.assertEqual(stays[0]["user_id"], "u")

    def test_dbscan_finds_two_clusters(self):
        rows = []
        for index, (lat, lon) in enumerate([(39.9, 116.3), (39.9005, 116.3004), (39.8997, 116.3002), (39.95, 116.45), (39.9504, 116.4502), (39.9498, 116.4504)]):
            rows.append({"user_id": str(index), "trajectory_id": f"t{index}", "start_ts": "2020-01-01T08:00:00Z", "end_ts": "2020-01-01T08:30:00Z", "duration_s": 1800, "latitude": lat, "longitude": lon, "radius_m": 20})
        hotspots = build_hotspots(rows, eps_m=500, min_pts=3)
        self.assertEqual(len(hotspots), 2)

    def test_trajectory_geometry(self):
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        row = trajectory_from_points("u", "t", [{"timestamp": start, "latitude": 39.9, "longitude": 116.3, "altitude_m": None}, {"timestamp": start + timedelta(minutes=1), "latitude": 39.91, "longitude": 116.31, "altitude_m": 10}])
        self.assertEqual(row["trajectory_id"], "t")
        self.assertEqual(row["geometry"]["type"], "LineString")
        self.assertGreater(row["distance_m"], 0)

    def test_write_dataset_keeps_previous_snapshot_on_serialization_error(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "demo.json"
            output.write_text(json.dumps({"version": "previous"}), encoding="utf-8")
            with self.assertRaises(TypeError):
                write_dataset({"not_json": object()}, output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"version": "previous"})
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
