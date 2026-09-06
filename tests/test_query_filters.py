import unittest

from backend.query_filters import filter_hotspots, filter_trajectories


class QueryFilterTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "trajectories": [
                {"trajectory_id": "a", "user_id": "u1", "start_ts": "2024-01-01T08:00:00Z", "end_ts": "2024-01-01T09:00:00Z", "geometry": {"type": "LineString", "coordinates": [[116.3, 39.9], [116.31, 39.91]]}, "points": []},
                {"trajectory_id": "b", "user_id": "u2", "start_ts": "2024-01-02T08:00:00Z", "end_ts": "2024-01-02T09:00:00Z", "geometry": {"type": "LineString", "coordinates": [[117.3, 40.9], [117.31, 40.91]]}, "points": []},
            ],
            "hotspots": [{"hotspot_id": "HS-01", "center": {"latitude": 39.9, "longitude": 116.3}, "visit_count": 10, "unique_users": 4}],
        }

    def test_trajectory_bbox_user_and_offset(self):
        rows = filter_trajectories(self.data, user_id="u1", bbox=(116.0, 39.0, 116.5, 40.0), limit=1)
        self.assertEqual([row["trajectory_id"] for row in rows], ["a"])
        self.assertEqual(filter_trajectories(self.data, offset=2), [])

    def test_hotspot_bbox_and_min_users(self):
        rows = filter_hotspots(self.data, bbox=(116.0, 39.0, 116.5, 40.0), min_users=4)
        self.assertEqual([row["hotspot_id"] for row in rows], ["HS-01"])


if __name__ == "__main__":
    unittest.main()
