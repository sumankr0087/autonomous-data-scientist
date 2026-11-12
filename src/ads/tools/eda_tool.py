"""EDA tool — deterministic (no-LLM) analysis helpers.

Given the SQL result (a DataFrame), compute a compact, structured set of findings
the EDA agent can reason over and narrate: shape, per-column summaries, the
extreme rows for the most important metric, and outlier/anomaly detection.

Kept generic so it works on *any* query result, not just the sample sales data.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ads.core.logging import get_logger

log = get_logger(__name__)

# Column-name hints for picking the "metric" to focus extremes/anomalies on.
_FOCUS_HINTS = ("change", "pct", "diff", "delta", "revenue", "rev", "sales", "total", "sum", "amount")


def _focus_column(df: pd.DataFrame) -> str | None:
    numeric = df.select_dtypes(include="number").columns.tolist()
    if not numeric:
        return None
    for hint in _FOCUS_HINTS:
        for col in numeric:
            if hint in col.lower():
                return col
    return numeric[-1]


def _numeric_summary(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if s.empty:
            continue
        out[col] = {
            "min": float(s.min()),
            "max": float(s.max()),
            "mean": round(float(s.mean()), 2),
            "sum": round(float(s.sum()), 2),
        }
    return out


def _extremes(df: pd.DataFrame, focus: str | None, n: int = 3) -> dict[str, list[dict]]:
    if not focus:
        return {}
    ordered = df.sort_values(focus)
    return {
        "lowest": ordered.head(n).to_dict("records"),
        "highest": ordered.tail(n).iloc[::-1].to_dict("records"),
    }


def _anomalies(df: pd.DataFrame, max_flagged: int = 10) -> list[dict[str, Any]]:
    """Flag rows that are IQR outliers on any numeric column."""
    flagged: list[dict[str, Any]] = []
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = np.percentile(s, [25, 75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[col] < lo) | (df[col] > hi)
        for _, row in df[mask].iterrows():
            flagged.append({"column": col, "value": float(row[col]), "row": row.to_dict()})
            if len(flagged) >= max_flagged:
                return flagged
    return flagged


def analyze_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Return a compact findings dict describing the DataFrame."""
    if df is None or df.empty:
        return {"empty": True, "rows": 0, "note": "No data returned by the query."}

    focus = _focus_column(df)
    findings = {
        "empty": False,
        "rows": int(len(df)),
        "columns": {c: str(t) for c, t in df.dtypes.items()},
        "focus_metric": focus,
        "numeric_summary": _numeric_summary(df),
        "extremes": _extremes(df, focus),
        "anomalies": _anomalies(df),
    }
    log.info(
        "EDA findings: rows=%d focus=%s anomalies=%d",
        findings["rows"], focus, len(findings["anomalies"]),
    )
    return findings
