"""ML agent.

Wraps the ML tool: builds a DataFrame from the query result and trains a baseline
model to surface drivers (feature importances) and headline metrics. Runs only
when the planner decided `needs_ml` is true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from ads.core.logging import get_logger
from ads.tools.ml_tool import MlOutcome, train_baseline

log = get_logger(__name__)


@dataclass
class MlResult:
    ran: bool
    summary: str = ""
    outcome: dict[str, Any] = field(default_factory=dict)


def run_ml(
    data: pd.DataFrame | list[dict],
    question: str,
    target: str | None = None,
) -> MlResult:
    df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data or [])
    outcome: MlOutcome = train_baseline(df, target=target)

    if not outcome.ok:
        log.info("ML skipped/failed: %s", outcome.note)
        return MlResult(ran=False, summary=outcome.note, outcome={"note": outcome.note})

    top = ", ".join(
        f"{d['feature']} ({d['importance']})" for d in outcome.importances[:5]
    )
    summary = (
        f"Trained a baseline {outcome.task} model on target '{outcome.target}'. "
        f"Metrics: {outcome.metrics}. Top drivers: {top}."
    )
    return MlResult(
        ran=True,
        summary=summary,
        outcome={
            "task": outcome.task,
            "target": outcome.target,
            "metrics": outcome.metrics,
            "importances": outcome.importances,
        },
    )
