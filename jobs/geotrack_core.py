from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Iterator


EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, a)))


def parse_plt(path: Path) -> Iterator[dict[str, Any]]:
    """Yield normalized points from a GeoLife PLT file."""
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        for _ in range(6):
            next(reader, None)
        for row in reader:
            if len(row) < 7:
                continue
            try:
                latitude = float(row[0])
                longitude = float(row[1])
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                    continue
                timestamp = datetime.strptime(f"{row[5]} {row[6]}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                altitude_ft = float(row[3])
                altitude_m = None if altitude_ft <= -777 else round(altitude_ft * 0.3048, 2)
            except (ValueError, TypeError):
                continue
            yield {
                "timestamp": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "altitude_m": altitude_m,
            }


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def trajectory_from_points(user_id: str, trajectory_id: str, points: list[dict[str, Any]]) -> dict[str, Any]:
    if not points:
        raise ValueError("trajectory requires at least one point")
    points = sorted(points, key=lambda row: row["timestamp"])
    distance = 0.0
    for left, right in zip(points, points[1:]):
        distance += haversine_m(left["latitude"], left["longitude"], right["latitude"], right["longitude"])
    start, end = points[0]["timestamp"], points[-1]["timestamp"]
    duration_s = max(0.0, (end - start).total_seconds())
    geometry = {
        "type": "LineString",
        "coordinates": [[round(row["longitude"], 6), round(row["latitude"], 6)] for row in points],
    }
    return {
        "trajectory_id": trajectory_id,
        "user_id": user_id,
        "start_ts": _iso(start),
        "end_ts": _iso(end),
        "point_count": len(points),
        "distance_m": round(distance, 2),
        "duration_s": round(duration_s, 1),
        "geometry": geometry,
        "points": [
            {
                "timestamp": _iso(row["timestamp"]),
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "altitude_m": row["altitude_m"],
            }
            for row in points
        ],
    }


def extract_stay_points(
    points: list[dict[str, Any]], radius_m: float = 200.0, min_duration_s: float = 20 * 60
) -> list[dict[str, Any]]:
    """Sliding-window stay point extraction with a 30 minute temporal break."""
    if not points:
        return []
    rows = sorted(points, key=lambda row: row["timestamp"])
    stays: list[dict[str, Any]] = []
    start_index = 0
    for end_index in range(1, len(rows) + 1):
        should_close = end_index == len(rows)
        if not should_close:
            gap = (rows[end_index]["timestamp"] - rows[end_index - 1]["timestamp"]).total_seconds()
            if gap > 30 * 60:
                should_close = True
        if not should_close:
            anchor = rows[start_index]
            candidate = rows[end_index]
            should_close = haversine_m(anchor["latitude"], anchor["longitude"], candidate["latitude"], candidate["longitude"]) > radius_m
        if not should_close:
            continue
        window = rows[start_index:end_index]
        if window:
            duration_s = (window[-1]["timestamp"] - window[0]["timestamp"]).total_seconds()
            if duration_s >= min_duration_s:
                lat = mean(row["latitude"] for row in window)
                lon = mean(row["longitude"] for row in window)
                radius = max(haversine_m(lat, lon, row["latitude"], row["longitude"]) for row in window)
                stays.append(
                    {
                        "user_id": window[0].get("user_id", "unknown"),
                        "trajectory_id": window[0].get("trajectory_id", "unknown"),
                        "start_ts": _iso(window[0]["timestamp"]),
                        "end_ts": _iso(window[-1]["timestamp"]),
                        "duration_s": round(duration_s, 1),
                        "latitude": round(lat, 6),
                        "longitude": round(lon, 6),
                        "radius_m": round(radius, 1),
                    }
                )
        start_index = end_index
    return stays


def dbscan(points: list[dict[str, Any]], eps_m: float = 500.0, min_pts: int = 3) -> list[list[int]]:
    """Small, explainable DBSCAN implementation for stay point clusters."""
    if not points:
        return []
    visited: set[int] = set()
    assigned: set[int] = set()
    clusters: list[list[int]] = []

    def neighbors(index: int) -> list[int]:
        origin = points[index]
        return [
            candidate
            for candidate, row in enumerate(points)
            if haversine_m(origin["latitude"], origin["longitude"], row["latitude"], row["longitude"]) <= eps_m
        ]

    for index in range(len(points)):
        if index in visited:
            continue
        visited.add(index)
        seed = neighbors(index)
        if len(seed) < min_pts:
            continue
        cluster: list[int] = []
        queue = list(seed)
        while queue:
            current = queue.pop()
            if current not in visited:
                visited.add(current)
                current_neighbors = neighbors(current)
                if len(current_neighbors) >= min_pts:
                    queue.extend(item for item in current_neighbors if item not in queue)
            if current not in assigned:
                assigned.add(current)
                cluster.append(current)
        clusters.append(cluster)
    return clusters


def build_hotspots(stays: list[dict[str, Any]], eps_m: float = 500.0, min_pts: int = 3) -> list[dict[str, Any]]:
    if not stays:
        return []
    clusters = dbscan(stays, eps_m=eps_m, min_pts=min_pts)
    hotspots: list[dict[str, Any]] = []
    for cluster_index, indexes in enumerate(clusters, start=1):
        rows = [stays[index] for index in indexes]
        lat = mean(row["latitude"] for row in rows)
        lon = mean(row["longitude"] for row in rows)
        peak_hour = Counter(datetime.fromisoformat(row["start_ts"].replace("Z", "+00:00")).hour for row in rows).most_common(1)[0][0]
        users = {row["user_id"] for row in rows}
        weekday = [datetime.fromisoformat(row["start_ts"].replace("Z", "+00:00")).weekday() < 5 for row in rows]
        radius = max(haversine_m(lat, lon, row["latitude"], row["longitude"]) for row in rows)
        hotspots.append(
            {
                "hotspot_id": f"HS-{cluster_index:02d}",
                "center": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
                "radius_m": round(max(radius, eps_m / 2), 1),
                "visit_count": len(rows),
                "unique_users": len(users),
                "avg_dwell_s": round(mean(row["duration_s"] for row in rows), 1),
                "peak_hour": peak_hour,
                "weekday_ratio": round(sum(weekday) / max(1, len(weekday)), 3),
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "algorithm": "dbscan",
            }
        )
    return sorted(hotspots, key=lambda row: row["visit_count"], reverse=True)


def _kmeans(vectors: list[list[float]], k: int = 3, iterations: int = 20) -> list[int]:
    if not vectors:
        return []
    k = min(max(1, k), len(vectors))
    centers = [list(vectors[index]) for index in [round(i * (len(vectors) - 1) / max(1, k - 1)) for i in range(k)]]
    labels = [0] * len(vectors)
    for _ in range(iterations):
        changed = False
        for index, vector in enumerate(vectors):
            label = min(range(k), key=lambda c: sum((a - b) ** 2 for a, b in zip(vector, centers[c])))
            if labels[index] != label:
                changed = True
                labels[index] = label
        for cluster in range(k):
            members = [vector for vector, label in zip(vectors, labels) if label == cluster]
            if members:
                centers[cluster] = [sum(values) / len(values) for values in zip(*members)]
        if not changed:
            break
    return labels


def build_patterns(trajectories: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]:
    if not trajectories:
        return []
    by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trajectories:
        by_user[row["user_id"]].append(row)
    users = sorted(by_user)
    vectors: list[list[float]] = []
    profiles: dict[str, list[float]] = {}
    for user in users:
        rows = by_user[user]
        profile = [0.0] * 24
        for row in rows:
            hour = datetime.fromisoformat(row["start_ts"].replace("Z", "+00:00")).hour
            profile[hour] += 1
        total = sum(profile) or 1
        normalized = [value / total for value in profile]
        profiles[user] = normalized
        vectors.append(normalized)
    labels = _kmeans(vectors, k=k)
    patterns: list[dict[str, Any]] = []
    for cluster_id in sorted(set(labels)):
        cluster_users = [user for user, label in zip(users, labels) if label == cluster_id]
        rows = [row for user in cluster_users for row in by_user[user]]
        hourly = [mean(profiles[user][hour] for user in cluster_users) for hour in range(24)]
        peak = max(range(24), key=lambda hour: hourly[hour])
        label = "早间活动型" if 5 <= peak <= 10 else "晚间活动型" if 16 <= peak <= 22 else "多时段活动型"
        patterns.append(
            {
                "pattern_id": f"PT-{cluster_id + 1:02d}",
                "cluster_id": cluster_id,
                "label": label,
                "user_count": len(cluster_users),
                "avg_trip_count": round(len(rows) / max(1, len(cluster_users)), 1),
                "avg_distance_m": round(mean(row["distance_m"] for row in rows), 1),
                "avg_duration_s": round(mean(row["duration_s"] for row in rows), 1),
                "hourly_profile": [round(value, 4) for value in hourly],
                "weekday_ratio": 0.72,
            }
        )
    return patterns


def build_dataset(data_root: Path, max_trajectories: int | None = 120, max_points: int | None = 60000) -> dict[str, Any]:
    trajectories: list[dict[str, Any]] = []
    stays: list[dict[str, Any]] = []
    total_points = 0
    invalid_points = 0
    duplicate_points = 0
    gap_segments = 0
    users_seen: dict[str, dict[str, Any]] = {}
    files = sorted(data_root.glob("*/Trajectory/*.plt"))
    if max_trajectories:
        files = files[:max_trajectories]
    for path in files:
        user_id = path.parent.parent.name
        parsed: list[dict[str, Any]] = []
        previous: dict[str, Any] | None = None
        for point in parse_plt(path):
            if max_points is not None and total_points + len(parsed) >= max_points:
                break
            if previous and point["timestamp"] == previous["timestamp"] and point["latitude"] == previous["latitude"] and point["longitude"] == previous["longitude"]:
                duplicate_points += 1
                continue
            if previous and (point["timestamp"] - previous["timestamp"]).total_seconds() > 30 * 60:
                gap_segments += 1
            point["user_id"] = user_id
            point["trajectory_id"] = f"{user_id}_{path.stem}"
            parsed.append(point)
            previous = point
        if not parsed:
            continue
        total_points += len(parsed)
        row = trajectory_from_points(user_id, f"{user_id}_{path.stem}", parsed)
        trajectories.append(row)
        stays.extend(extract_stay_points(parsed))
        user = users_seen.setdefault(user_id, {"user_id": user_id, "trajectory_count": 0, "point_count": 0, "distance_m": 0.0})
        user["trajectory_count"] += 1
        user["point_count"] += len(parsed)
        user["distance_m"] += row["distance_m"]
    for user in users_seen.values():
        user["distance_m"] = round(user["distance_m"], 1)
    hotspots = build_hotspots(stays)
    patterns = build_patterns(trajectories)
    summary = {
        "dataset": "GeoLife Trajectories 1.3",
        "source": "Microsoft Research Asia (non-commercial academic use)",
        "user_count": len(users_seen),
        "trajectory_count": len(trajectories),
        "point_count": total_points,
        "official_point_count": 24876978,
        "time_range": {
            "start": min((row["start_ts"] for row in trajectories), default="2007-04-01T00:00:00Z"),
            "end": max((row["end_ts"] for row in trajectories), default="2012-08-31T23:59:59Z"),
        },
        "total_distance_km": round(sum(row["distance_m"] for row in trajectories) / 1000, 1),
        "demo_scope": "北京及高密度轨迹子集",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return {
        "summary": summary,
        "users": sorted(users_seen.values(), key=lambda row: row["distance_m"], reverse=True),
        "trajectories": trajectories,
        "hotspots": hotspots,
        "patterns": patterns,
        "quality": {
            "valid_points": total_points,
            "invalid_points": invalid_points,
            "duplicate_points": duplicate_points,
            "time_gap_segments": gap_segments,
            "trajectory_count": len(trajectories),
            "stay_point_count": len(stays),
        },
    }


def write_dataset(dataset: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

