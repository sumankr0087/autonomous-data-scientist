"""Tests for Step 7 (ML agent) and Step 8 (viz + report), offline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ads.agents.ml_agent import run_ml
from ads.agents.report_agent import compose
from ads.tools.ml_tool import train_baseline
from ads.tools.viz_tool import make_charts


def _synthetic_regression(n=200):
    rng = np.random.default_rng(0)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    cat = rng.choice(["a", "b", "c"], size=n)
    # target strongly driven by x1
    y = 5 * x1 + 0.5 * x2 + rng.normal(scale=0.1, size=n)
    return pd.DataFrame({"x1": x1, "x2": x2, "cat": cat, "target": y})


def test_ml_trains_and_ranks_drivers():
    df = _synthetic_regression()
    out = train_baseline(df, target="target")
    assert out.ok is True
    assert out.task == "regression"
    assert out.metrics["r2"] > 0.8
    # x1 should be the top driver.
    assert out.importances[0]["feature"] == "x1"


def test_ml_agent_insufficient_rows():
    df = pd.DataFrame({"a": [1, 2, 3], "target": [1.0, 2.0, 3.0]})
    res = run_ml(df, "predict target")
    assert res.ran is False
    assert "Insufficient" in res.summary


def test_make_charts_creates_png(tmp_path, monkeypatch):
    import config.settings as settings_mod
    import ads.tools.viz_tool as viz

    monkeypatch.setattr(viz, "ARTIFACTS_DIR", tmp_path)
    rows = [
        {"category": "A", "channel": "Online", "revenue_change": -500.0},
        {"category": "B", "channel": "Retail", "revenue_change": 120.0},
        {"category": "C", "channel": "Partner", "revenue_change": -50.0},
    ]
    paths = make_charts(rows, run_id="test")
    assert len(paths) == 1
    assert paths[0].endswith(".png")


def test_report_compose_offline(tmp_path, monkeypatch):
    import ads.agents.report_agent as rep

    monkeypatch.setattr(rep, "ARTIFACTS_DIR", tmp_path)
    res = compose(
        question="Why did sales drop?",
        plan=["step 1", "step 2"],
        eda_narrative="- Online sales collapsed.",
        ml_summary="",
        charts=["chart.png"],
        run_id="t1",
    )
    assert "Executive Report" in res.markdown
    assert "Online sales collapsed" in res.markdown
    assert res.path and res.path.endswith("report_t1.md")
