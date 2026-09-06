"""Serving repository implementations for SQLite fallback and PostGIS."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any, Iterator

from .full_index_store import FullIndexStore


class PostgresFullRepository:
    """Read the currently published batch from PostGIS.

    Connections are short-lived and strictly read-only at this layer; batch
    publication itself is owned by ``jobs/load_full_serving.py``.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn

    @contextmanager
    def _db(self) -> Iterator[Any]:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as error:  # pragma: no cover
            raise RuntimeError("Postgres serving 需要 psycopg") from error
        with psycopg.connect(self.dsn, options="-c default_transaction_read_only=on", row_factory=dict_row) as connection:
            yield connection

    def _run_id(self, connection: Any) -> str | None:
        row = connection.execute("SELECT run_id FROM current_run WHERE singleton").fetchone()
        return row["run_id"] if row else None

    @property
    def is_ready(self) -> bool:
        try:
            with self._db() as connection:
                return self._run_id(connection) is not None
        except Exception:
            return False

    @property
    def full_summary(self) -> dict[str, Any]:
        with self._db() as connection:
            run_id = self._run_id(connection)
            if not run_id:
                return {"available": False}
            row = connection.execute("SELECT dataset, source, counts, quality, started_at, finished_at FROM batch_runs WHERE run_id=%s", (run_id,)).fetchone()
            if not row:
                return {"available": False}
            counts = row["counts"] or {}
            quality = row["quality"] or {}
            summary = {
                "dataset": row["dataset"], "source": row["source"], "run_id": run_id,
                "user_count": counts.get("users", counts.get("user_count", 0)),
                "trajectory_count": counts.get("trajectories", 0),
                "point_count": counts.get("trajectory_points", 0),
                "stay_point_count": counts.get("stay_points", 0),
                "hotspot_count": counts.get("hotspots", 0),
            }
            return {"available": True, "summary": summary, "quality": quality, "run_id": run_id, "published_at": row["finished_at"].isoformat() if row["finished_at"] else None}

    def users(self, query: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self._db() as connection:
            run_id = self._run_id(connection)
            if not run_id:
                return []
            sql = "SELECT user_id, trajectory_count, point_count, distance_m, run_id FROM users WHERE run_id=%s"
            params: list[Any] = [run_id]
            if query:
                sql += " AND user_id ILIKE %s"; params.append(f"%{query}%")
            sql += " ORDER BY distance_m DESC LIMIT %s"; params.append(max(1, min(limit, 500)))
            return [
                {**dict(row), "distance_m": float(row["distance_m"] or 0)}
                for row in connection.execute(sql, params).fetchall()
            ]

    def trajectories(self, user_id: str | None = None, start: str | None = None, end: str | None = None, limit: int = 20, offset: int = 0, bbox: tuple[float, float, float, float] | None = None) -> list[dict[str, Any]]:
        with self._db() as connection:
            run_id = self._run_id(connection)
            if not run_id:
                return []
            clauses = ["run_id=%s"]; params: list[Any] = [run_id]
            if user_id: clauses.append("user_id=%s"); params.append(user_id)
            if start: clauses.append("end_ts >= %s"); params.append(start)
            if end: clauses.append("start_ts <= %s"); params.append(end)
            if bbox:
                west, south, east, north = bbox
                clauses.append("geom && ST_MakeEnvelope(%s,%s,%s,%s,4326)"); params.extend([west, south, east, north])
            sql = "SELECT trajectory_id,user_id,start_ts,end_ts,point_count,distance_m,duration_s,run_id,ST_AsGeoJSON(geom) AS geometry_json FROM trajectories WHERE " + " AND ".join(clauses) + " ORDER BY start_ts LIMIT %s OFFSET %s"
            params.extend([max(1, min(limit, 200)), max(0, offset)])
            result = []
            for row in connection.execute(sql, params).fetchall():
                item = dict(row)
                geometry_json = item.pop("geometry_json", None)
                item["geometry"] = json.loads(geometry_json) if geometry_json else None
                result.append(item)
            return result

    def trajectory(self, trajectory_id: str, sample_limit: int = 500) -> dict[str, Any] | None:
        with self._db() as connection:
            run_id = self._run_id(connection)
            if not run_id:
                return None
            row = connection.execute("SELECT trajectory_id,user_id,start_ts,end_ts,point_count,distance_m,duration_s,run_id,ST_AsGeoJSON(geom) AS geometry_json FROM trajectories WHERE trajectory_id=%s AND run_id=%s", (trajectory_id, run_id)).fetchone()
            if not row:
                return None
            item = dict(row)
            geometry_json = item.pop("geometry_json", None)
            item["geometry"] = json.loads(geometry_json) if geometry_json else None
            limit = max(1, min(sample_limit, 2000))
            points = connection.execute("""WITH ranked AS (
              SELECT seq,ts AS timestamp,latitude,longitude,altitude_m,
                     row_number() OVER (ORDER BY seq) AS rn,
                     count(*) OVER () AS total
              FROM trajectory_points WHERE trajectory_id=%s AND run_id=%s
            ), sampled AS (
              SELECT *, GREATEST(1, CEIL(total::numeric / %s)::bigint) AS stride
              FROM ranked
            ) SELECT seq,timestamp,latitude,longitude,altitude_m,total FROM sampled
              WHERE rn=1 OR rn=total OR ((rn-1) % stride)=0
              ORDER BY seq LIMIT %s""", (trajectory_id, run_id, limit, limit)).fetchall()
            item["points"] = [{**dict(point), "timestamp": point["timestamp"].isoformat().replace("+00:00", "Z") if point["timestamp"] else None} for point in points]
            item["sampled"] = len(points) < item["point_count"]
            item["sample_limit"] = limit
            return item

    def hotspots(self, limit: int = 20, min_users: int = 0) -> list[dict[str, Any]]:
        with self._db() as connection:
            run_id = self._run_id(connection)
            if not run_id: return []
            rows = connection.execute("SELECT hotspot_id,visit_count,unique_users,avg_dwell_s,peak_hour,weekday_ratio,algorithm,run_id,ST_AsGeoJSON(center_geom) AS center_json,ST_AsGeoJSON(geometry) AS geometry_json FROM hotspots WHERE run_id=%s AND unique_users >= %s ORDER BY visit_count DESC, unique_users DESC LIMIT %s", (run_id, min_users, max(1, min(limit, 200)))).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["center"] = json.loads(item.pop("center_json"))
                item["geometry"] = json.loads(item.pop("geometry_json"))
                result.append(item)
            return result

    def patterns(self) -> list[dict[str, Any]]:
        with self._db() as connection:
            run_id = self._run_id(connection)
            if not run_id: return []
            rows = connection.execute("SELECT pattern_id,cluster_id,label,user_count,avg_trip_count,avg_distance_m,avg_duration_s,hourly_profile,weekday_ratio,run_id FROM temporal_patterns WHERE run_id=%s ORDER BY cluster_id", (run_id,)).fetchall()
            return [dict(row) for row in rows]

    def quality(self) -> dict[str, Any]:
        return self.full_summary.get("quality", {})


def repository() -> Any:
    if os.getenv("GEOTRACK_SERVING_BACKEND", "sqlite").lower() == "postgres":
        return PostgresFullRepository(os.getenv("DATABASE_URL", "postgresql://geotrack:geotrack@localhost:5432/geotrack"))
    from .full_data import FULL_INDEX_PATH
    return FullIndexStore(FULL_INDEX_PATH)
