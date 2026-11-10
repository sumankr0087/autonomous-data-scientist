"""Workflow node functions.

Step 3 scope: these are **stubs** that wire the graph end to end. Each node logs
its activation, records that it ran, and passes state through. In later steps,
each stub is replaced by its real agent (planner, SQL, EDA, ML, viz, report).

A node takes the current `GraphState` and returns a dict of updates to merge.
"""

from __future__ import annotations

from ads.core.constants import AgentName
from ads.core.logging import bind, get_logger
from ads.graph.state import GraphState

log = get_logger(__name__)


def _run_log(state: GraphState):
    return bind(log, run_id=state.get("run_id", "?"))


def planner_node(state: GraphState) -> dict:
    """Real planner: question + schema -> ordered plan + step flags."""
    from ads.agents.planner import plan as make_plan
    from ads.tools.sql_tool import SQLTool

    rlog = _run_log(state)
    rlog.info("[planner] planning")
    schema = SQLTool().get_schema()
    result = make_plan(state["question"], schema)
    rlog.info("[planner] %s", result.rationale or "plan ready")
    return {
        "plan": result.steps,
        "needs_ml": result.needs_ml,
        "rationale": result.rationale,
        "status": "planned",
        "steps_completed": [AgentName.PLANNER.value],
    }


def sql_node(state: GraphState) -> dict:
    _run_log(state).info("[sql_agent] generating & running SQL (stub)")
    return {"status": "queried", "steps_completed": [AgentName.SQL.value]}


def eda_node(state: GraphState) -> dict:
    _run_log(state).info("[eda_agent] profiling & detecting anomalies (stub)")
    return {"status": "analyzed", "steps_completed": [AgentName.EDA.value]}


def ml_node(state: GraphState) -> dict:
    _run_log(state).info("[ml_agent] training baseline model (stub)")
    return {"status": "modeled", "steps_completed": [AgentName.ML.value]}


def viz_node(state: GraphState) -> dict:
    _run_log(state).info("[viz_agent] creating charts (stub)")
    return {"status": "visualized", "steps_completed": [AgentName.VIZ.value]}


def report_node(state: GraphState) -> dict:
    _run_log(state).info("[report_agent] composing report (stub)")
    report = (
        "# Report (stub)\n\n"
        f"Question: {state.get('question', '')}\n\n"
        "The full report is generated once the agents are implemented "
        "(Steps 4-8)."
    )
    return {"report": report, "status": "completed", "steps_completed": [AgentName.REPORT.value]}
