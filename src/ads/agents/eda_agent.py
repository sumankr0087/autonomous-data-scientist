"""EDA agent.

Turns the SQL result into findings (via `eda_tool`) and a short, business-ready
narrative. The statistics are deterministic; the narrative is written by the LLM
(with an offline template fallback so the pipeline never hard-fails).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from ads.core.exceptions import RateLimitError
from ads.core.logging import get_logger
from ads.llm.client import BaseLLMClient, get_llm_client
from ads.tools.eda_tool import analyze_dataframe

log = get_logger(__name__)


@dataclass
class EdaResult:
    findings: dict[str, Any] = field(default_factory=dict)
    narrative: str = ""


SYSTEM = (
    "You are a data analyst. Given structured findings from a dataset, you write a "
    "concise, factual summary of the key insights in plain business English."
)

PROMPT = """\
Business question: {question}

Structured findings (JSON):
{findings}

Write 3-5 short bullet points summarising the most important insights, focusing on
the biggest changes, extremes and anomalies. Be specific and quantitative. Return
plain text bullets only."""


def _template_narrative(findings: dict[str, Any]) -> str:
    if findings.get("empty"):
        return "- The query returned no rows, so there is nothing to analyse."
    lines = [f"- The result has {findings['rows']} rows."]
    focus = findings.get("focus_metric")
    extremes = findings.get("extremes", {})
    if focus and extremes.get("lowest"):
        low = extremes["lowest"][0]
        lines.append(f"- Lowest `{focus}`: {low.get(focus)} ({low}).")
    if focus and extremes.get("highest"):
        high = extremes["highest"][0]
        lines.append(f"- Highest `{focus}`: {high.get(focus)} ({high}).")
    if findings.get("anomalies"):
        lines.append(f"- {len(findings['anomalies'])} anomaly/outlier row(s) detected.")
    return "\n".join(lines)


def analyze(
    data: pd.DataFrame | list[dict],
    question: str,
    llm: BaseLLMClient | None = None,
) -> EdaResult:
    """Compute findings and a concise narrative for the query result.

    The narrative is built deterministically (no LLM call) to save the free-tier
    quota — the report agent still turns these findings into a full written report.
    Pass `llm` explicitly to opt into an LLM-written narrative.
    """
    df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data or [])
    findings = analyze_dataframe(df)

    if llm is None:
        return EdaResult(findings=findings, narrative=_template_narrative(findings))

    try:
        prompt = PROMPT.format(
            question=question,
            findings=json.dumps(findings, default=str)[:6000],
        )
        narrative = llm.complete(prompt, system=SYSTEM, max_tokens=4000).text.strip()
        if not narrative:
            raise ValueError("empty narrative")
        return EdaResult(findings=findings, narrative=narrative)
    except RateLimitError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.warning("EDA narrative via LLM failed, using template: %s", exc)
        return EdaResult(findings=findings, narrative=_template_narrative(findings))
