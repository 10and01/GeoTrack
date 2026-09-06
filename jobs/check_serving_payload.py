"""Inspect serving-table row counts without requiring database packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def counts(input_path: Path) -> dict[str, int]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    trajectories = data.get("trajectories", [])
    stay_points = data.get("stay_points", [])
    hotspots = data.get("hotspots", [])
    return {
        "trajectory_points": sum(len(row.get("points", [])) for row in trajectories),
        "trajectories": len(trajectories),
        "stay_points": len(stay_points),
        "hotspots": len(hotspots),
        "temporal_patterns": len(data.get("patterns", [])),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/demo.json"))
    args = parser.parse_args()
    print(json.dumps(counts(args.input), ensure_ascii=False))
