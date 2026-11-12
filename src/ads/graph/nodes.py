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
    """Real SQL agent: generate -> run -> self-correct, store rows in state."""
    from ads.agents.sql_agent import answer as sql_answer

    rlog = _run_log(state)
    rlog.info("[sql_agent] generating & running SQL")
    result = sql_answer(state["question"], plan=state.get("plan"))

    if not result.ok:
        rlog.error("[sql_agent] failed after %d attempts: %s", result.attempts, result.error)
        return {
            "status": "sql_failed",
            "errors": [f"sql_agent: {result.error}"],
            "steps_completed": [AgentName.SQL.value],
        }

    rlog.info("[sql_agent] %d rows (attempt %d)", result.row_count, result.attempts)
    return {
        "sql": result.sql,
        "query_result": result.rows,
        "query_columns": result.columns,
        "row_count": result.row_count,
        "status": "queried",
        "steps_completed": [AgentName.SQL.value],
    }


def eda_node(state: GraphState) -> dict:
    """Real EDA agent: findings + narrative from the SQL result."""
    from ads.agents.eda_agent import analyze

    rlog = _run_log(state)
    rlog.info("[eda_agent] profiling & detecting anomalies")
    rows = state.get("query_result", [])
    result = analyze(rows, state["question"])
    rlog.info("[eda_agent] %d anomalies", len(result.findings.get("anomalies", [])))
    return {
        "eda": {"findings": result.findings, "narrative": result.narrative},
        "status": "analyzed",
        "steps_completed": [AgentName.EDA.value],
    }


def ml_node(state: GraphState) -> dict:
    """Train a baseline model — only when the planner flagged needs_ml."""
    rlog = _run_log(state)
    if not state.get("needs_ml"):
        rlog.info("[ml_agent] skipped (needs_ml=False)")
        return {
            "ml": {"ran": False, "summary": "ML not required for this question."},
            "status": "modeled",
            "steps_completed": [AgentName.ML.value],
        }

    from ads.agents.ml_agent import run_ml

    rlog.info("[ml_agent] training baseline model")
    result = run_ml(state.get("query_result", []), state["question"])
    rlog.info("[ml_agent] %s", result.summary)
    return {
        "ml": {"ran": result.ran, "summary": result.summary, **result.outcome},
        "status": "modeled",
        "steps_completed": [AgentName.ML.value],
    }


def viz_node(state: GraphState) -> dict:
    """Render charts from the SQL result into artifacts/."""
    from ads.tools.viz_tool import make_charts

    rlog = _run_log(state)
    rlog.info("[viz_agent] creating charts")
    paths = make_charts(state.get("query_result", []), run_id=state.get("run_id", "run"))
    rlog.info("[viz_agent] %d chart(s)", len(paths))
    return {"viz": paths, "status": "visualized", "steps_completed": [AgentName.VIZ.value]}


def report_node(state: GraphState) -> dict:
    """Compose the executive report from everything the pipeline produced."""
    from config.settings import get_settings

    from ads.agents.report_agent import compose
    from ads.graph.workflow import get_approver

    rlog = _run_log(state)

    # Human-in-the-loop gate before producing the final report.
    if get_settings().enable_human_approval:
        approver = get_approver()
        if approver is not None and not approver(state):
            rlog.warning("[report_agent] rejected by human approver")
            return {
                "status": "rejected",
                "errors": ["report_agent: rejected by human approver"],
                "steps_completed": [AgentName.REPORT.value],
            }

    rlog.info("[report_agent] composing report")
    eda = (state.get("eda") or {}).get("narrative", "")
    ml = (state.get("ml") or {}).get("summary", "")
    result = compose(
        question=state["question"],
        plan=state.get("plan"),
        eda_narrative=eda,
        ml_summary=ml,
        charts=state.get("viz"),
        run_id=state.get("run_id", "run"),
    )
    return {
        "report": result.markdown,
        "report_path": result.path or "",
        "status": "completed",
        "steps_completed": [AgentName.REPORT.value],
    }
