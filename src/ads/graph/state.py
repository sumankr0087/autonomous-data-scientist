"""Shared workflow state.

Every agent node reads from and writes to this single typed object as it flows
through the LangGraph. Fields annotated with `operator.add` *accumulate* across
nodes (e.g. errors, completed steps); all others are overwritten by the latest
node that sets them.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class GraphState(TypedDict, total=False):
    # --- inputs ---
    run_id: str
    question: str

    # --- produced by the agents ---
    plan: list[str]            # planner  -> ordered steps
    needs_ml: bool             # planner  -> whether the ML step is required
    rationale: str             # planner  -> one-line plan rationale
    sql: str                   # sql_agent -> generated query
    query_result: list[dict]   # sql_agent -> rows as records
    eda: dict[str, Any]        # eda_agent -> findings (trends, anomalies)
    ml: dict[str, Any]         # ml_agent  -> model results / drivers
    viz: list[str]             # viz_agent -> chart file paths
    report: str                # report_agent -> final markdown report

    # --- control / observability ---
    status: str
    steps_completed: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]


def initial_state(question: str, run_id: str) -> GraphState:
    """Build the starting state for a run."""
    return GraphState(
        run_id=run_id,
        question=question,
        status="started",
        steps_completed=[],
        errors=[],
    )
