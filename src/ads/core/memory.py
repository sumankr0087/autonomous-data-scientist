"""Run memory — persist each completed run so history can be reviewed/reused.

Each run is written as JSON to `artifacts/history/<run_id>.json`. This is the
lightweight 'memory' component: it lets the app list past questions, reuse prior
results, and audit what the agents did.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import ARTIFACTS_DIR

from ads.core.logging import get_logger

log = get_logger(__name__)

HISTORY_DIR = Path(ARTIFACTS_DIR) / "history"


def _summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state.get("run_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": state.get("question"),
        "status": state.get("status"),
        "needs_ml": state.get("needs_ml"),
        "row_count": state.get("row_count"),
        "sql": state.get("sql"),
        "eda": (state.get("eda") or {}).get("narrative"),
        "ml": (state.get("ml") or {}).get("summary"),
        "report_path": state.get("report_path"),
        "charts": state.get("viz"),
    }


def save_run(state: dict[str, Any]) -> str | None:
    """Persist a completed run's summary. Returns the file path (or None)."""
    try:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        run_id = state.get("run_id", "run")
        path = HISTORY_DIR / f"{run_id}.json"
        path.write_text(json.dumps(_summary(state), indent=2, default=str), encoding="utf-8")
        log.info("Saved run to memory: %s", path)
        return str(path)
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not save run memory: %s", exc)
        return None


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent run summaries, newest first."""
    if not HISTORY_DIR.exists():
        return []
    runs: list[dict[str, Any]] = []
    for f in sorted(HISTORY_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            runs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
        if len(runs) >= limit:
            break
    return runs
