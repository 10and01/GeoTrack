from __future__ import annotations

import argparse
import json
from pathlib import Path

import psycopg


def load(output: Path, dsn: str) -> None:
    data = json.loads(output.read_text(encoding="utf-8"))
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            for row in data.get("trajectories", []):
                coordinates = row.get("geometry", {}).get("coordinates", [])
                if not coordinates:
                    continue
                line_wkt = "LINESTRING(" + ",".join(f"{lon} {lat}" for lon, lat in coordinates) + ")"
                cursor.execute(
                    """
                    INSERT INTO trajectories
                      (trajectory_id, user_id, start_ts, end_ts, point_count, distance_m, duration_s, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
                    ON CONFLICT (trajectory_id) DO UPDATE SET
                      point_count = EXCLUDED.point_count,
                      distance_m = EXCLUDED.distance_m,
                      duration_s = EXCLUDED.duration_s,
                      geom = EXCLUDED.geom
                    """,
                    (
                        row["trajectory_id"], row["user_id"], row["start_ts"], row["end_ts"],
                        row["point_count"], row["distance_m"], row["duration_s"], line_wkt,
                    ),
                )
            for row in data.get("hotspots", []):
                lon, lat = row["geometry"]["coordinates"]
                cursor.execute(
                    """
                    INSERT INTO hotspots
                      (hotspot_id, center_geom, geometry, visit_count, unique_users, avg_dwell_s,
                       peak_hour, weekday_ratio, algorithm, run_id)
                    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                            ST_Buffer(ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)::geometry,
                            %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hotspot_id) DO UPDATE SET
                      visit_count = EXCLUDED.visit_count,
                      unique_users = EXCLUDED.unique_users,
                      avg_dwell_s = EXCLUDED.avg_dwell_s
                    """,
                    (
                        row["hotspot_id"], lon, lat, lon, lat, row["radius_m"],
                        row["visit_count"], row["unique_users"], row["avg_dwell_s"],
                        row["peak_hour"], row["weekday_ratio"], row.get("algorithm", "dbscan"),
                        data.get("summary", {}).get("generated_at", "local"),
                    ),
                )
        connection.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/demo.json"))
    parser.add_argument("--dsn", default="postgresql://geotrack:geotrack@localhost:5432/geotrack")
    args = parser.parse_args()
    load(args.input, args.dsn)
    print("loaded", args.input)
