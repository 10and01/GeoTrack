"""Load all precomputed demo artifacts into the PostGIS serving schema."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any



def _wkt_line(coordinates: list[list[float]]) -> str:
    return "LINESTRING(" + ",".join(f"{lon} {lat}" for lon, lat in coordinates) + ")"


def _point_rows(data: dict[str, Any]):
    for trajectory in data.get("trajectories", []):
        for seq, point in enumerate(trajectory.get("points", [])):
            yield trajectory, seq, point


def load(input_path: Path, dsn: str, run_id: str | None = None, dry_run: bool = False) -> dict[str, int]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    trajectories = data.get("trajectories", [])
    point_rows = list(_point_rows(data))
    stay_points = data.get("stay_points", [])
    hotspots = data.get("hotspots", [])
    patterns = data.get("patterns", [])
    counts = {
        "trajectory_points": len(point_rows),
        "trajectories": len(trajectories),
        "stay_points": len(stay_points),
        "hotspots": len(hotspots),
        "temporal_patterns": len(patterns),
    }
    if dry_run:
        return counts

    if not dry_run:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("写入数据库需要 psycopg；仅检查载荷时请使用 --dry-run") from error
    batch_id = run_id or data.get("summary", {}).get("generated_at", datetime.utcnow().isoformat())
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        for trajectory in trajectories:
            coordinates = trajectory.get("geometry", {}).get("coordinates", [])
            if not coordinates:
                continue
            cursor.execute(
                """
                INSERT INTO trajectories
                  (trajectory_id, user_id, start_ts, end_ts, point_count, distance_m, duration_s, geom)
                VALUES (%s,%s,%s,%s,%s,%s,%s,ST_GeomFromText(%s,4326))
                ON CONFLICT (trajectory_id) DO UPDATE SET
                  user_id=EXCLUDED.user_id,start_ts=EXCLUDED.start_ts,end_ts=EXCLUDED.end_ts,
                  point_count=EXCLUDED.point_count,distance_m=EXCLUDED.distance_m,
                  duration_s=EXCLUDED.duration_s,geom=EXCLUDED.geom
                """,
                (trajectory["trajectory_id"], trajectory["user_id"], trajectory["start_ts"], trajectory["end_ts"],
                 trajectory["point_count"], trajectory["distance_m"], trajectory["duration_s"], _wkt_line(coordinates)),
            )
        for trajectory, seq, point in point_rows:
            cursor.execute(
                """
                INSERT INTO trajectory_points
                  (user_id,trajectory_id,seq,ts,latitude,longitude,altitude_m)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (trajectory_id,seq) DO UPDATE SET
                  ts=EXCLUDED.ts,latitude=EXCLUDED.latitude,longitude=EXCLUDED.longitude,altitude_m=EXCLUDED.altitude_m
                """,
                (trajectory["user_id"], trajectory["trajectory_id"], seq, point["timestamp"], point["latitude"], point["longitude"], point.get("altitude_m")),
            )
        for stay in stay_points:
            cursor.execute(
                """
                INSERT INTO stay_points
                  (user_id, trajectory_id, start_ts, end_ts, duration_s, center_geom, radius_m)
                SELECT %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s
                WHERE NOT EXISTS (
                  SELECT 1 FROM stay_points
                  WHERE trajectory_id = %s AND start_ts = %s AND end_ts = %s
                )
                """,
                (stay["user_id"], stay["trajectory_id"], stay["start_ts"], stay["end_ts"],
                 stay["duration_s"], stay["longitude"], stay["latitude"], stay["radius_m"],
                 stay["trajectory_id"], stay["start_ts"], stay["end_ts"]),
            )
        for hotspot in hotspots:
            lon, lat = hotspot["geometry"]["coordinates"]
            cursor.execute(
                """
                INSERT INTO hotspots
                  (hotspot_id,center_geom,geometry,visit_count,unique_users,avg_dwell_s,peak_hour,weekday_ratio,algorithm,run_id)
                VALUES (%s,ST_SetSRID(ST_MakePoint(%s,%s),4326),
                        ST_Buffer(ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)::geometry,
                        %s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (hotspot_id) DO UPDATE SET
                  center_geom=EXCLUDED.center_geom,geometry=EXCLUDED.geometry,visit_count=EXCLUDED.visit_count,
                  unique_users=EXCLUDED.unique_users,avg_dwell_s=EXCLUDED.avg_dwell_s,peak_hour=EXCLUDED.peak_hour,
                  weekday_ratio=EXCLUDED.weekday_ratio,algorithm=EXCLUDED.algorithm,run_id=EXCLUDED.run_id
                """,
                (hotspot["hotspot_id"], lon, lat, lon, lat, hotspot.get("radius_m", 500), hotspot["visit_count"],
                 hotspot["unique_users"], hotspot["avg_dwell_s"], hotspot["peak_hour"], hotspot["weekday_ratio"],
                 hotspot.get("algorithm", "dbscan"), batch_id),
            )
        for pattern in patterns:
            cursor.execute(
                """
                INSERT INTO temporal_patterns
                  (pattern_id,cluster_id,label,user_count,avg_trip_count,avg_distance_m,avg_duration_s,hourly_profile,weekday_ratio,run_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
                ON CONFLICT (pattern_id) DO UPDATE SET
                  cluster_id=EXCLUDED.cluster_id,label=EXCLUDED.label,user_count=EXCLUDED.user_count,
                  avg_trip_count=EXCLUDED.avg_trip_count,avg_distance_m=EXCLUDED.avg_distance_m,
                  avg_duration_s=EXCLUDED.avg_duration_s,hourly_profile=EXCLUDED.hourly_profile,
                  weekday_ratio=EXCLUDED.weekday_ratio,run_id=EXCLUDED.run_id
                """,
                (pattern["pattern_id"], pattern["cluster_id"], pattern["label"], pattern["user_count"],
                 pattern["avg_trip_count"], pattern["avg_distance_m"], pattern["avg_duration_s"],
                 json.dumps(pattern["hourly_profile"]), pattern["weekday_ratio"], batch_id),
            )
        connection.commit()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/demo.json"))
    parser.add_argument("--dsn", default="postgresql://geotrack:geotrack@localhost:5432/geotrack")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(load(args.input, args.dsn, args.run_id, args.dry_run), ensure_ascii=False))
