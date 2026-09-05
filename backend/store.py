from __future__ import annotations

import json
import math
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Hotspot, Pattern, Trajectory


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "demo.json"
SEED_FILE = ROOT / "data" / "demo_seed.json"


def _read_json() -> dict[str, Any]:
    source = DATA_FILE if DATA_FILE.exists() else SEED_FILE
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"summary": {}, "trajectories": [], "hotspots": [], "patterns": [], "users": []}


class GeoTrackStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        with self._lock:
            self.data = _read_json()

    @property
    def summary(self) -> dict[str, Any]:
        return self.data.get("summary", {})

    def users(self, query: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        users = self.data.get("users", [])
        if query:
            users = [u for u in users if query.lower() in str(u.get("user_id", "")).lower()]
        return users[: max(1, min(limit, 500))]

    def trajectories(
        self,
        user_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = self.data.get("trajectories", [])
        if user_id:
            rows = [row for row in rows if row.get("user_id") == user_id]
        if start:
            rows = [row for row in rows if row.get("end_ts", "") >= start]
        if end:
            rows = [row for row in rows if row.get("start_ts", "") <= end]
        return rows[: max(1, min(limit, 200))]

    def trajectory(self, trajectory_id: str) -> dict[str, Any] | None:
        return next((row for row in self.data.get("trajectories", []) if row.get("trajectory_id") == trajectory_id), None)

    def hotspots(self, limit: int = 20, min_users: int = 0) -> list[dict[str, Any]]:
        rows = [row for row in self.data.get("hotspots", []) if row.get("unique_users", 0) >= min_users]
        rows.sort(key=lambda row: (row.get("visit_count", 0), row.get("unique_users", 0)), reverse=True)
        return rows[: max(1, min(limit, 200))]

    def patterns(self) -> list[dict[str, Any]]:
        return self.data.get("patterns", [])

    def quality(self) -> dict[str, Any]:
        quality = self.data.get("quality", {})
        return quality or {
            "valid_points": self.summary.get("point_count", 0),
            "invalid_points": 0,
            "duplicate_points": 0,
            "time_gap_segments": 0,
            "trajectory_count": self.summary.get("trajectory_count", 0),
        }

    def create_job(self, job_type: str) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "message": "任务已加入本地演示队列。完整环境中由 Spark submit 执行。",
        }
        with self._lock:
            self._jobs[job_id] = job
        return job

    def job(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)


store = GeoTrackStore()

