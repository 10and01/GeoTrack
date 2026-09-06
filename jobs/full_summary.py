"""Bounded-memory full GeoLife scan.

This command deliberately does *not* build the demo JSON shape.  The complete
GeoLife release contains tens of millions of points, so a single JSON document
would be both slow and unsafe to load in the API process.  Instead, it scans
one PLT file at a time and writes a small, reproducible manifest.  The manifest
is useful as the local fallback and as evidence before submitting the same
input to :mod:`spark_distributed`.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:  # Works both as `python jobs/full_summary.py` and as a package import.
    from .geotrack_core import haversine_m
except ImportError:  # pragma: no cover - script execution path
    from geotrack_core import haversine_m


def _parse_row(row: list[str]) -> tuple[datetime, float, float, float | None] | None:
    if len(row) < 7:
        return None
    try:
        latitude = float(row[0])
        longitude = float(row[1])
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None
        timestamp = datetime.strptime(f"{row[5]} {row[6]}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        altitude_ft = float(row[3])
        altitude_m = None if altitude_ft <= -777 else round(altitude_ft * 0.3048, 2)
    except (TypeError, ValueError):
        return None
    return timestamp, latitude, longitude, altitude_m


def scan_file(path: Path) -> dict[str, Any]:
    """Return quality counters for one PLT without retaining all points."""
    user_id = path.parent.parent.name
    trajectory_id = f"{user_id}_{path.stem}"
    raw_rows = invalid_points = duplicate_points = gap_segments = 0
    valid_points = 0
    distance_m = 0.0
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    previous: tuple[datetime, float, float, float | None] | None = None

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        for _ in range(6):
            next(reader, None)
        for row in reader:
            raw_rows += 1
            point = _parse_row(row)
            if point is None:
                invalid_points += 1
                continue
            timestamp, latitude, longitude, altitude_m = point
            if previous and timestamp == previous[0] and latitude == previous[1] and longitude == previous[2]:
                duplicate_points += 1
                continue
            if previous:
                gap_s = (timestamp - previous[0]).total_seconds()
                if gap_s > 30 * 60:
                    gap_segments += 1
                distance_m += haversine_m(previous[1], previous[2], latitude, longitude)
            if first_ts is None:
                first_ts = timestamp
            last_ts = timestamp
            previous = point
            valid_points += 1

    return {
        "user_id": user_id,
        "trajectory_id": trajectory_id,
        "raw_rows": raw_rows,
        "valid_points": valid_points,
        "invalid_points": invalid_points,
        "duplicate_points": duplicate_points,
        "time_gap_segments": gap_segments,
        "distance_m": round(distance_m, 2),
        "start_ts": first_ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if first_ts else None,
        "end_ts": last_ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if last_ts else None,
    }


def iter_plt_files(data_root: Path) -> Iterator[Path]:
    yield from sorted(data_root.glob("*/Trajectory/*.plt"))


def scan_dataset(data_root: Path) -> dict[str, Any]:
    files = list(iter_plt_files(data_root))
    file_reports: list[dict[str, Any]] = []
    for path in files:
        file_reports.append(scan_file(path))

    users = {report["user_id"] for report in file_reports}
    valid_reports = [report for report in file_reports if report["valid_points"] > 0]
    starts = [report["start_ts"] for report in valid_reports if report["start_ts"]]
    ends = [report["end_ts"] for report in valid_reports if report["end_ts"]]
    manifest = {
        "dataset": "GeoLife Trajectories 1.3",
        "source": "Microsoft Research Asia (non-commercial academic use)",
        "data_root": str(data_root),
        "processed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "processing_mode": "local-full-scan",
        "official": {
            "user_count": 182,
            "trajectory_count": 18670,
            "point_count": 24876978,
        },
        "counts": {
            "user_count": len(users),
            "plt_file_count": len(files),
            "trajectory_count": len(valid_reports),
            "valid_point_count": sum(report["valid_points"] for report in file_reports),
            "raw_row_count": sum(report["raw_rows"] for report in file_reports),
            "invalid_point_count": sum(report["invalid_points"] for report in file_reports),
            "duplicate_point_count": sum(report["duplicate_points"] for report in file_reports),
            "time_gap_segment_count": sum(report["time_gap_segments"] for report in file_reports),
            "total_distance_m": round(sum(report["distance_m"] for report in file_reports), 2),
        },
        "time_range": {"start": min(starts) if starts else None, "end": max(ends) if ends else None},
        "quality_rules": {
            "header_lines_skipped": 6,
            "timezone": "UTC (GeoLife timestamps documented as GMT)",
            "invalid_coordinates_dropped": True,
            "continuous_duplicates_dropped": True,
            "time_gap_threshold_s": 1800,
            "altitude_sentinel": -777,
        },
        "next_step": {
            "spark_input": "hdfs:///geotrack/raw/Data/*/Trajectory/*.plt",
            "spark_output": "hdfs:///geotrack/curated/points",
            "spark_quality_output": "hdfs:///geotrack/curated/quality",
        },
        # Per-file reports are compact (~a few MB) and make quality findings
        # auditable without storing point-level data in Git or the API.
        "files": file_reports,
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan all GeoLife PLT files into a bounded-size manifest")
    parser.add_argument("--data-root", type=Path, default=Path("Geolife Trajectories 1.3/Data"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/full-manifest.json"))
    args = parser.parse_args()
    if not args.data_root.exists():
        raise SystemExit(f"数据目录不存在: {args.data_root}")
    manifest = scan_dataset(args.data_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), **manifest["counts"], "time_range": manifest["time_range"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()


