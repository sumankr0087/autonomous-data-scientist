"""The /run route: executes the agent workflow for a question."""

from __future__ import annotations

import base64
from pathlib import Path

from fastapi import APIRouter

from ads.api.catalog import default_model
from ads.api.schemas import RunRequest
from ads.core.logging import get_logger
from ads.graph.workflow import run_workflow

log = get_logger(__name__)
router = APIRouter()


def _charts_as_data_urls(paths: list[str]) -> list[str]:
    out: list[str] = []
    for c in paths or []:
        p = Path(c)
        if p.exists():
            out.append("data:image/png;base64," + base64.b64encode(p.read_bytes()).decode())
    return out


@router.post("/run")
def run(req: RunRequest) -> dict:
    from config.settings import get_settings

    from ads.core.exceptions import RateLimitError
    from ads.llm.client import set_llm_override

    s = get_settings()
    provider = req.provider or s.llm_provider
    model = req.model or (default_model(provider) if req.provider else s.llm_model)

    if not s.key_for(provider):
        return {
            "status": "error",
            "error": f"No API key configured on the server for provider '{provider}'.",
            "question": req.question,
        }

    set_llm_override(provider, model)
    try:
        result = run_workflow(req.question)
    except RateLimitError as exc:
        when = f" Try again in about {exc.retry_after}." if exc.retry_after else " Please try again later."
        window_word = {"day": "daily", "hour": "hourly", "minute": "per-minute"}.get(exc.window or "", "")
        window = f" (the {window_word} free AI limit was reached)" if window_word else ""
        suggest = ""
        if provider != "groq" and s.key_for("groq"):
            suggest = " You can switch the model to Groq (top-right) and try again now."
        log.warning("Rate limited (%s): %s", provider, exc.details)
        return {
            "status": "rate_limited",
            "message": f"The {provider} usage limit has been reached{window}.{when}{suggest}",
            "retry_after": exc.retry_after,
            "window": exc.window,
            "question": req.question,
        }
    except Exception as exc:  # noqa: BLE001 - surface the real cause to the client
        log.exception("Run failed")
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}", "question": req.question}
    finally:
        set_llm_override(None, None)

    return {
        "status": result.get("status"),
        "question": req.question,
        "plan": result.get("plan", []),
        "needs_ml": result.get("needs_ml"),
        "rationale": result.get("rationale"),
        "sql": result.get("sql"),
        "row_count": result.get("row_count"),
        "columns": result.get("query_columns", []),
        "rows": (result.get("query_result") or [])[:200],
        "eda": (result.get("eda") or {}).get("narrative"),
        "ml": result.get("ml"),
        "report": result.get("report"),
        "charts": _charts_as_data_urls(result.get("viz", [])),
    }
