"""FastAPI routes for filtered trajectories and hotspots."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .query_filters import filter_hotspots, filter_trajectories
from .store import store

router = APIRouter(prefix="/api/query", tags=["filtered queries"])


def _bbox(west: float | None, south: float | None, east: float | None, north: float | None):
    values = (west, south, east, north)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values) or west > east or south > north:
        raise HTTPException(status_code=422, detail="invalid bounding box")
    return (west, south, east, north)


@router.get("/trajectories")
def filtered_trajectories(
    user_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    west: float | None = Query(None, ge=-180, le=180),
    south: float | None = Query(None, ge=-90, le=90),
    east: float | None = Query(None, ge=-180, le=180),
    north: float | None = Query(None, ge=-90, le=90),
) -> list[dict[str, Any]]:
    return filter_trajectories(store.data, user_id, start, end, limit, offset, _bbox(west, south, east, north), include_points=False)


@router.get("/hotspots")
def filtered_hotspots(
    limit: int = Query(20, ge=1, le=200),
    min_users: int = Query(0, ge=0),
    user_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    eps: float = Query(500.0, ge=50, le=5000),
    min_pts: int = Query(3, ge=1, le=1000, alias="minPts"),
    west: float | None = Query(None, ge=-180, le=180),
    south: float | None = Query(None, ge=-90, le=90),
    east: float | None = Query(None, ge=-180, le=180),
    north: float | None = Query(None, ge=-90, le=90),
) -> list[dict[str, Any]]:
    return filter_hotspots(store.data, limit, min_users, user_id, start, end, _bbox(west, south, east, north), eps, min_pts)
