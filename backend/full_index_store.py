"""SQLite-backed full-data serving store.

The browser never receives the raw GeoLife corpus.  It receives paged
trajectory summaries and a bounded sample of points from the generated
``full-serving.sqlite`` index.  PostgreSQL/PostGIS remains the production
serving target; SQLite is the local fallback that makes the full dataset
demonstrable without Docker.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class FullIndexStore:
    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        # All access is read-only.  Besides documenting the serving contract,
        # URI mode prevents a typo or missing generated artifact from creating
        # an empty SQLite file as a side effect of an API request.
        connection = sqlite3.connect(f"file:{self.path.resolve().as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _metadata(self, key: str, default: Any) -> Any:
        try:
            with self._connection() as connection:
                row = connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
            return json.loads(row["value"]) if row else default
        except (OSError, sqlite3.Error, json.JSONDecodeError):
            return default

    @property
    def is_ready(self) -> bool:
        """Return whether the generated file has the serving schema and data."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return False
        try:
            with self._connection() as connection:
                tables = {
                    row["name"]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
            required = {"metadata", "users", "trajectories", "trajectory_points", "hotspots", "patterns"}
            summary = self.summary
            return required.issubset(tables) and isinstance(summary, dict) and "trajectory_count" in summary
        except (OSError, sqlite3.Error):
            return False

    @property
    def summary(self) -> dict[str, Any]:
        return self._metadata("summary", {})

    @property
    def full_summary(self) -> dict[str, Any]:
        return {"available": True, "summary": self.summary, "quality": self.quality(), "parameters": self._metadata("manifest", {}).get("parameters", {})}

    def users(self, query: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        sql = "SELECT user_id, trajectory_count, point_count, distance_m FROM users"
        params: list[Any] = []
        if query:
            sql += " WHERE user_id LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY distance_m DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with self._connection() as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def trajectories(self, user_id: str | None = None, start: str | None = None, end: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if user_id:
            clauses.append("user_id = ?"); params.append(user_id)
        if start:
            clauses.append("end_ts >= ?"); params.append(start)
        if end:
            clauses.append("start_ts <= ?"); params.append(end)
        sql = "SELECT * FROM trajectories" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY start_ts LIMIT ? OFFSET ?"
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connection() as connection:
            rows = []
            for row in connection.execute(sql, params):
                item = dict(row)
                item["geometry"] = json.loads(item.pop("geometry_json"))
                item.pop("sample_stride", None)
                rows.append(item)
            return rows

    def trajectory(self, trajectory_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM trajectories WHERE trajectory_id = ?", (trajectory_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            item["geometry"] = json.loads(item.pop("geometry_json"))
            points = connection.execute("SELECT seq, ts AS timestamp, latitude, longitude, altitude_m FROM trajectory_points WHERE trajectory_id = ? ORDER BY seq", (trajectory_id,)).fetchall()
            item["points"] = [dict(point) for point in points]
            item["sampled"] = len(item["points"]) < int(item.get("point_count", len(item["points"])))
            item["sample_limit"] = len(item["points"])
            return item

    def hotspots(self, limit: int = 20, min_users: int = 0) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM hotspots WHERE unique_users >= ? ORDER BY visit_count DESC, unique_users DESC LIMIT ?", (min_users, max(1, min(limit, 200)))).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["center"] = json.loads(item.pop("center_json"))
            item["geometry"] = json.loads(item.pop("geometry_json"))
            result.append(item)
        return result

    def patterns(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM patterns ORDER BY cluster_id").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["hourly_profile"] = json.loads(item.pop("hourly_profile_json"))
            result.append(item)
        return result

    def quality(self) -> dict[str, Any]:
        return self._metadata("quality", {})
