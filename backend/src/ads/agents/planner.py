"""Planner agent.

Turns a business question + the warehouse schema into a concrete, ordered plan
and decides which downstream steps are actually needed (e.g. skip ML for a
simple lookup). This is the first LLM-powered agent.

Design notes
------------
- The LLM is asked to return **strict JSON**; we parse it defensively (strip
  markdown fences, slice to the outer braces) and validate with pydantic.
- If the LLM is unavailable (no key / offline / parse failure), we fall back to
  a sensible default plan so the pipeline never hard-fails on planning.
- `plan(..., llm=...)` accepts an injected client so tests run without a network.
"""

from __future__ import annotations

import json
import os
import re

from pydantic import BaseModel, Field, ValidationError

from ads.core.exceptions import RateLimitError
from ads.core.logging import get_logger
from ads.llm.client import BaseLLMClient, get_llm_client

log = get_logger(__name__)


class PlanResult(BaseModel):
    steps: list[str] = Field(default_factory=list)
    needs_sql: bool = True
    needs_ml: bool = False
    needs_viz: bool = True
    rationale: str = ""


SYSTEM = (
    "You are a senior data scientist. You plan how to answer a business question "
    "using a SQL analytics database. You think about which steps are truly needed "
    "and you respond with STRICT JSON only — no prose, no markdown."
)

PROMPT_TEMPLATE = """\
A business user asked:
\"{question}\"

The database schema is:
{schema}

Produce a short analysis plan. Return ONLY a JSON object with these keys:
- "steps": array of 3-6 short imperative step strings
- "needs_sql": boolean (almost always true)
- "needs_ml": boolean (true ONLY if the question needs prediction/forecasting or
  finding drivers/causes via a model; false for simple aggregation/lookup)
- "needs_viz": boolean (true if charts would help)
- "rationale": one short sentence explaining the plan

Respond with JSON only.
"""


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of an LLM reply (tolerant of ```json fences)."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM reply")
    return json.loads(cleaned[start : end + 1])


def _default_plan(question: str) -> PlanResult:
    needs_ml = bool(
        re.search(r"\b(predict|forecast|driver|cause|why|influence|factor)\b", question.lower())
    )
    return PlanResult(
        steps=[
            "Query the relevant sales data for the question",
            "Run exploratory analysis (trends, anomalies, group comparisons)",
            *(["Train a model to identify drivers"] if needs_ml else []),
            "Visualize the key findings",
            "Write an executive report",
        ],
        needs_sql=True,
        needs_ml=needs_ml,
        needs_viz=True,
        rationale="Default plan (LLM planner unavailable).",
    )


def plan(question: str, schema: str, llm: BaseLLMClient | None = None) -> PlanResult:
    """Return a `PlanResult` for the question. Falls back to a default plan."""
    # Offline guard (used by the test-suite) and explicit injection for tests.
    if llm is None and os.getenv("ADS_DISABLE_LLM"):
        return _default_plan(question)

    try:
        client = llm or get_llm_client()
        resp = client.complete(PROMPT_TEMPLATE.format(question=question, schema=schema), system=SYSTEM)
        result = PlanResult(**_extract_json(resp.text))
        if not result.steps:
            raise ValueError("Planner returned no steps")
        log.info("Planner produced %d steps (needs_ml=%s)", len(result.steps), result.needs_ml)
        return result
    except RateLimitError:
        raise
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        log.warning("Planner parse/validation failed, using default plan: %s", exc)
        return _default_plan(question)
    except Exception as exc:  # noqa: BLE001 - LLM/config failure
        log.warning("Planner LLM unavailable, using default plan: %s", exc)
        return _default_plan(question)
