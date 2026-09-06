"""Optional full-index API wiring helpers."""

from __future__ import annotations

import os
from pathlib import Path

from .full_index_store import FullIndexStore


ROOT = Path(__file__).resolve().parents[1]
FULL_INDEX_PATH = Path(os.getenv("GEOTRACK_FULL_INDEX", str(ROOT / "data" / "processed" / "full-serving.sqlite")))
full_index_store = FullIndexStore(FULL_INDEX_PATH)
