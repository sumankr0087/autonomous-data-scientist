"""Tests for the Step 3 LangGraph workflow skeleton."""

from __future__ import annotations

from ads.core.constants import AgentName
from ads.graph.state import initial_state
from ads.graph.workflow import build_workflow, run_workflow


def test_initial_state():
    s = initial_state("why did sales drop?", run_id="r1")
    assert s["question"] == "why did sales drop?"
    assert s["status"] == "started"
    assert s["steps_completed"] == []


def test_workflow_compiles():
    graph = build_workflow()
    assert graph is not None


def test_workflow_runs_all_nodes_in_order():
    result = run_workflow("Why did sales drop in Maharashtra last quarter?", run_id="t1")
    expected = [
        AgentName.PLANNER.value,
        AgentName.SQL.value,
        AgentName.EDA.value,
        AgentName.ML.value,
        AgentName.VIZ.value,
        AgentName.REPORT.value,
    ]
    assert result["steps_completed"] == expected
    assert result["status"] == "completed"
    assert "plan" in result and len(result["plan"]) >= 3
    assert result["report"].startswith("# Report")
