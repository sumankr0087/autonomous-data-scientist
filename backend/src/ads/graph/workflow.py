"""LangGraph workflow definition.

Wires the agent nodes into a linear pipeline:

    START -> planner -> sql -> eda -> ml -> viz -> report -> END

Later steps may add conditional edges (e.g. skip ML when not needed) and a
human-approval interrupt before side-effecting steps.
"""

from __future__ import annotations

import uuid
from typing import Callable

from langgraph.graph import END, START, StateGraph

from ads.core.constants import AgentName
from ads.core.logging import bind, get_logger
from ads.graph.nodes import (
    eda_node,
    ml_node,
    planner_node,
    report_node,
    sql_node,
    viz_node,
)
from ads.graph.state import GraphState, initial_state

log = get_logger(__name__)


def build_workflow():
    """Build and compile the LangGraph state machine."""
    g = StateGraph(GraphState)

    g.add_node(AgentName.PLANNER.value, planner_node)
    g.add_node(AgentName.SQL.value, sql_node)
    g.add_node(AgentName.EDA.value, eda_node)
    g.add_node(AgentName.ML.value, ml_node)
    g.add_node(AgentName.VIZ.value, viz_node)
    g.add_node(AgentName.REPORT.value, report_node)

    g.add_edge(START, AgentName.PLANNER.value)
    g.add_edge(AgentName.PLANNER.value, AgentName.SQL.value)
    g.add_edge(AgentName.SQL.value, AgentName.EDA.value)
    g.add_edge(AgentName.EDA.value, AgentName.ML.value)
    g.add_edge(AgentName.ML.value, AgentName.VIZ.value)
    g.add_edge(AgentName.VIZ.value, AgentName.REPORT.value)
    g.add_edge(AgentName.REPORT.value, END)

    return g.compile()


# Human-in-the-loop approver, consulted before the final report when
# `enable_human_approval` is on. Defaults to auto-approve.
_APPROVER: Callable[[GraphState], bool] | None = None


def set_approver(func: Callable[[GraphState], bool] | None) -> None:
    """Register (or clear) the human-approval callback used by `report_node`."""
    global _APPROVER
    _APPROVER = func


def get_approver() -> Callable[[GraphState], bool] | None:
    return _APPROVER


def run_workflow(
    question: str,
    run_id: str | None = None,
    approver: Callable[[GraphState], bool] | None = None,
) -> GraphState:
    """Execute the full workflow for a business question."""
    run_id = run_id or uuid.uuid4().hex[:8]
    rlog = bind(log, run_id=run_id)
    rlog.info("Starting workflow for question: %s", question)

    set_approver(approver)
    try:
        graph = build_workflow()
        result: GraphState = graph.invoke(initial_state(question, run_id))
    finally:
        set_approver(None)

    rlog.info(
        "Workflow finished: status=%s, steps=%s",
        result.get("status"),
        result.get("steps_completed"),
    )

    # Memory: persist the completed run.
    from ads.core.memory import save_run

    save_run(dict(result))
    return result
