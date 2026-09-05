from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Point(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    altitude_m: float | None = None


class Trajectory(BaseModel):
    trajectory_id: str
    user_id: str
    start_ts: str
    end_ts: str
    point_count: int
    distance_m: float
    duration_s: float
    geometry: dict[str, Any]
    points: list[Point] = Field(default_factory=list)


class Hotspot(BaseModel):
    hotspot_id: str
    center: dict[str, float]
    radius_m: float
    visit_count: int
    unique_users: int
    avg_dwell_s: float
    peak_hour: int
    weekday_ratio: float
    geometry: dict[str, Any]
    algorithm: str = "dbscan"


class Pattern(BaseModel):
    pattern_id: str
    cluster_id: int
    label: str
    user_count: int
    avg_trip_count: float
    avg_distance_m: float
    avg_duration_s: float
    hourly_profile: list[float]
    weekday_ratio: float


class JobRequest(BaseModel):
    job_type: Literal["ingest", "mine"] = "mine"
    max_trajectories: int | None = Field(default=None, ge=1)
    max_points: int | None = Field(default=None, ge=100)

