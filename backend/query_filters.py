"""Query-time filters for the local serving payload."""

from __future__ import annotations

from typing import Any

BBox = tuple[float, float, float, float]


def _trajectory_in_bbox(row: dict[str, Any], bbox: BBox | None) -> bool:
    if bbox is None:
        return True
    west, south, east, north = bbox
    return any(
        west <= coordinate[0] <= east and south <= coordinate[1] <= north
        for coordinate in row.get("geometry", {}).get("coordinates", [])
        if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2
    )


def filter_trajectories(
    data: dict[str, Any],
    user_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 20,
    offset: int = 0,
    bbox: BBox | None = None,
) -> list[dict[str, Any]]:
    rows = list(data.get("trajectories", []))
    if user_id:
        rows = [row for row in rows if row.get("user_id") == user_id]
    if start:
        rows = [row for row in rows if row.get("end_ts", "") >= start]
    if end:
        rows = [row for row in rows if row.get("start_ts", "") <= end]
    rows = [row for row in rows if _trajectory_in_bbox(row, bbox)]
    safe_limit = max(1, min(limit, 200))
    safe_offset = max(0, offset)
    return rows[safe_offset : safe_offset + safe_limit]


def _hotspot_center(row: dict[str, Any]) -> tuple[float, float]:
    center = row.get("center")
    if isinstance(center, dict):
        return float(center.get("longitude", 0)), float(center.get("latitude", 0))
    coordinates = row.get("geometry", {}).get("coordinates", [])
    if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
        return float(coordinates[0]), float(coordinates[1])
    return 0.0, 0.0


def filter_hotspots(
    data: dict[str, Any],
    limit: int = 20,
    min_users: int = 0,
    user_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    bbox: BBox | None = None,
    eps_m: float = 500.0,
    min_pts: int = 3,
) -> list[dict[str, Any]]:
    # A bbox is a read-time filter. Only user/time/custom DBSCAN parameters
    # require rebuilding the demo subset.
    custom = any((user_id, start, end)) or eps_m != 500.0 or min_pts != 3
    if custom:
        from jobs.geotrack_core import build_hotspots, extract_stay_points

        stays: list[dict[str, Any]] = []
        for trajectory in filter_trajectories(data, user_id=user_id, start=start, end=end, limit=200):
            from datetime import datetime

            points = []
            for point in trajectory.get("points", []):
                normalized = {
                    **point,
                    "user_id": trajectory.get("user_id"),
                    "trajectory_id": trajectory.get("trajectory_id"),
                }
                timestamp = normalized.get("timestamp")
                if isinstance(timestamp, str):
                    normalized["timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                points.append(normalized)
            stays.extend(extract_stay_points(points))
        rows = build_hotspots(stays, eps_m=eps_m, min_pts=min_pts)
    else:
        rows = list(data.get("hotspots", []))

    if bbox is not None:
        west, south, east, north = bbox
        rows = [
            row for row in rows
            if south <= _hotspot_center(row)[1] <= north and west <= _hotspot_center(row)[0] <= east
        ]
    rows = [row for row in rows if row.get("unique_users", 0) >= min_users]
    rows.sort(key=lambda row: (row.get("visit_count", 0), row.get("unique_users", 0)), reverse=True)
    return rows[: max(1, min(limit, 200))]
