"""Tests for Step 9 run memory."""

from __future__ import annotations

import ads.core.memory as memory


def test_save_and_list_run(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "HISTORY_DIR", tmp_path / "history")
    state = {
        "run_id": "abc123",
        "question": "Why did sales drop?",
        "status": "completed",
        "needs_ml": False,
        "row_count": 27,
        "sql": "SELECT 1",
        "eda": {"narrative": "- things dropped"},
        "ml": {"summary": "n/a"},
        "viz": ["chart.png"],
        "report_path": "report.md",
    }
    path = memory.save_run(state)
    assert path is not None

    runs = memory.list_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == "abc123"
    assert runs[0]["eda"] == "- things dropped"


def test_list_runs_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "HISTORY_DIR", tmp_path / "nope")
    assert memory.list_runs() == []
