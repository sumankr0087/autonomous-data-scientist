"""Tests for the Step 6 EDA agent + tool (offline; no LLM)."""

from __future__ import annotations

import pandas as pd

from ads.agents.eda_agent import analyze
from ads.tools.eda_tool import analyze_dataframe


def test_focus_metric_prefers_change_column():
    df = pd.DataFrame(
        {"category": ["A", "B", "C"], "revenue_change": [-500.0, 10.0, 300.0], "n": [1, 2, 3]}
    )
    f = analyze_dataframe(df)
    assert f["focus_metric"] == "revenue_change"
    # Lowest should be the most negative change.
    assert f["extremes"]["lowest"][0]["revenue_change"] == -500.0


def test_anomaly_detected():
    # One huge outlier among small values.
    df = pd.DataFrame({"g": list("abcdefghij"), "value": [1, 2, 3, 2, 1, 2, 3, 2, 1, 9999]})
    f = analyze_dataframe(df)
    assert any(a["value"] == 9999 for a in f["anomalies"])


def test_empty_dataframe():
    f = analyze_dataframe(pd.DataFrame())
    assert f["empty"] is True
    assert f["rows"] == 0


def test_analyze_returns_narrative_offline():
    rows = [
        {"channel": "Online", "revenue_change": -45000.0},
        {"channel": "Retail", "revenue_change": 1200.0},
    ]
    res = analyze(rows, "Why did sales drop?")
    assert res.findings["rows"] == 2
    assert res.narrative  # template narrative, non-empty
    assert "rows" in res.narrative


def test_analyze_empty_rows():
    res = analyze([], "anything")
    assert res.findings["empty"] is True
    assert "no rows" in res.narrative.lower()
