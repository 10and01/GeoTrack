"""Small read-only adapter for the full-data manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FULL_MANIFEST_FILE = ROOT / "data" / "processed" / "full-manifest.json"


def read_full_manifest() -> dict[str, Any] | None:
    if not FULL_MANIFEST_FILE.exists():
        return None
    try:
        data = json.loads(FULL_MANIFEST_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return {
        "dataset": data.get("dataset"),
        "source": data.get("source"),
        "processing_mode": data.get("processing_mode"),
        "processed_at": data.get("processed_at"),
        "official": data.get("official", {}),
        "counts": data.get("counts", {}),
        "time_range": data.get("time_range", {}),
        "quality_rules": data.get("quality_rules", {}),
        "next_step": data.get("next_step", {}),
    }
