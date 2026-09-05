"""Spark entry point for the course's distributed execution layer.

The local implementation is intentionally import-safe when PySpark is not installed.
In the Docker image, replace the small adapter below with Spark DataFrame writes to
HDFS/Parquet and reuse the same core algorithm parameters.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from geotrack_core import build_dataset, write_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed/demo.json"))
    parser.add_argument("--max-trajectories", type=int, default=None)
    parser.add_argument("--max-points", type=int, default=None)
    args = parser.parse_args()
    dataset = build_dataset(args.data_root, args.max_trajectories, args.max_points)
    write_dataset(dataset, args.output)
    print("spark_pipeline completed", dataset["summary"])


if __name__ == "__main__":
    main()

