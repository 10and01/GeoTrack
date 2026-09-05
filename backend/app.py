from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:  # pragma: no cover - gives a helpful import error when deps are missing
    FastAPI = None  # type: ignore[assignment]

from .models import JobRequest
from .store import store


if FastAPI is None:  # pragma: no cover
    raise RuntimeError("FastAPI is not installed. Run: uv pip install -r requirements.txt")


app = FastAPI(
    title="GeoTrack API",
    version="0.1.0",
    description="GeoLife GPS 轨迹清洗、热点分析与出行模式服务。",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "data_source": "processed-demo" if store.data else "empty"}


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    return store.summary


@app.get("/api/users")
def users(q: str | None = None, limit: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
    return store.users(q, limit)


@app.get("/api/trajectories")
def trajectories(
    user_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = Query(20, ge=1, le=200),
) -> list[dict[str, Any]]:
    return store.trajectories(user_id, start, end, limit)


@app.get("/api/trajectories/{trajectory_id}")
def trajectory(trajectory_id: str) -> dict[str, Any]:
    row = store.trajectory(trajectory_id)
    if not row:
        raise HTTPException(status_code=404, detail="trajectory not found")
    return row


@app.get("/api/hotspots")
def hotspots(
    limit: int = Query(20, ge=1, le=200),
    min_users: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    return store.hotspots(limit, min_users)


@app.get("/api/patterns/time")
def time_patterns() -> dict[str, Any]:
    rows = store.patterns()
    hourly = [0.0] * 24
    for row in rows:
        for index, value in enumerate(row.get("hourly_profile", [])[:24]):
            hourly[index] += float(value)
    total = sum(hourly) or 1
    return {"hourly_profile": [round(value / total, 4) for value in hourly], "patterns": rows}


@app.get("/api/patterns/clusters")
def cluster_patterns() -> list[dict[str, Any]]:
    return store.patterns()


@app.get("/api/data-quality")
def data_quality() -> dict[str, Any]:
    return store.quality()


@app.post("/api/jobs/run")
def run_job(request: JobRequest) -> dict[str, Any]:
    return store.create_job(request.job_type, request.max_trajectories, request.max_points)


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    job = store.job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

