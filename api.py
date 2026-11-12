"""Uvicorn entry point: adds `src/` to the path, then exposes the FastAPI app.

Run:  uvicorn api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ads.api import app  # noqa: E402,F401
