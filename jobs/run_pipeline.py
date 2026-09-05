from __future__ import annotations

import argparse
from pathlib import Path

from geotrack_core import build_dataset, write_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GeoTrack demo artifacts from GeoLife PLT files")
    parser.add_argument("--data-root", type=Path, default=Path("Geolife Trajectories 1.3/Data"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/demo.json"))
    parser.add_argument("--max-trajectories", type=int, default=120)
    parser.add_argument("--max-points", type=int, default=60000)
    parser.add_argument("--mine-only", action="store_true", help="kept for Makefile compatibility")
    args = parser.parse_args()
    if not args.data_root.exists():
        raise SystemExit(f"数据目录不存在: {args.data_root}")
    print(f"[GeoTrack] reading {args.data_root}")
    dataset = build_dataset(args.data_root, args.max_trajectories, args.max_points)
    write_dataset(dataset, args.output)
    print(f"[GeoTrack] wrote {args.output}")
    print(dataset["summary"])


if __name__ == "__main__":
    main()

