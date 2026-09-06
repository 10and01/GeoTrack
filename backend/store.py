from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
        page = rows[: max(1, min(limit, 200))]
        return [{key: value for key, value in row.items() if key != "points"} for row in page]

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

    def _update_job(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    def _run_job(self, job_id: str, job_type: str, max_trajectories: int | None, max_points: int | None) -> None:
        try:
            self._update_job(
                job_id,
                status="running",
                started_at=datetime.now(timezone.utc).isoformat(),
                message="正在执行本地批处理：解析、清洗、停留点和热点挖掘。",
            )
            from jobs.geotrack_core import build_dataset, write_dataset

            data_root = Path(os.getenv("GEOTRACK_DATA_ROOT", str(ROOT / "Geolife Trajectories 1.3" / "Data")))
            if not data_root.exists():
                raise FileNotFoundError(f"数据目录不存在: {data_root}")
            dataset = build_dataset(
                data_root,
                max_trajectories if max_trajectories is not None else int(os.getenv("GEOTRACK_DEMO_MAX_TRAJECTORIES", "120")),
                max_points if max_points is not None else int(os.getenv("GEOTRACK_DEMO_MAX_POINTS", "60000")),
            )
            write_dataset(dataset, DATA_FILE)
            self.reload()
            self._update_job(
                job_id,
                status="completed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                message="批处理完成，服务表已刷新。",
                summary=dataset.get("summary", {}),
            )
        except Exception as error:
            self._update_job(
                job_id,
                status="failed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                message="批处理失败。",
                error=str(error),
            )

    def create_job(self, job_type: str, max_trajectories: int | None = None, max_points: int | None = None) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "message": "任务已加入队列。",
        }
        with self._lock:
            self._jobs[job_id] = job
        worker = threading.Thread(
            target=self._run_job,
            args=(job_id, job_type, max_trajectories, max_points),
            daemon=True,
            name=f"geotrack-job-{job_id}",
        )
        worker.start()
        return dict(job)

    def job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None


store = GeoTrackStore()
