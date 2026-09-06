import tempfile
import unittest
from pathlib import Path

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover - dependency is in production requirements
    pa = None
    pq = None

from jobs.load_full_serving import inspect


@unittest.skipIf(pa is None, "pyarrow is not installed")
class FullServingTests(unittest.TestCase):
    def test_inspect_reads_partitioned_parquet_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "curated"
            for name, rows in {
                "points": [{"run_id": "run-1", "user_id": "001", "trajectory_id": "001_a", "seq": 0, "ts": "2008-01-01T00:00:00Z", "latitude": 39.9, "longitude": 116.3, "altitude_m": 10.0}],
                "trajectories": [{"run_id": "run-1", "user_id": "001", "trajectory_id": "001_a", "start_ts": "2008-01-01T00:00:00Z", "end_ts": "2008-01-01T00:01:00Z", "point_count": 1, "distance_m": 0.0, "duration_s": 60.0, "geom_wkt": "LINESTRING(116.3 39.9,116.3 39.9)"}],
            }.items():
                path = root / name
                path.mkdir(parents=True)
                pq.write_table(pa.Table.from_pylist(rows), path / "part-000.parquet")
            result = inspect(root)
            self.assertEqual(result["counts"]["trajectory_points"], 1)
            self.assertEqual(result["counts"]["trajectories"], 1)
            self.assertEqual(result["counts"]["stay_points"], 0)


if __name__ == "__main__":
    unittest.main()
