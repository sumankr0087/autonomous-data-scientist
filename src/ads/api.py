"""FastAPI backend for the Autonomous Data Scientist.

Exposes the agent workflow as a JSON API so a static React/Next frontend can call
it. The LLM API key stays on this server (never in the browser).

Run locally:  uvicorn api:app --reload   (from the repo root)
"""

from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ads.core.logging import get_logger
from ads.data.seed import seed_database
from ads.graph.workflow import run_workflow
from ads.tools.database import Database

log = get_logger(__name__)

EXAMPLES = [
    "Why did sales drop in Maharashtra last quarter?",
    "Which product categories grew the most in 2025?",
    "What factors drive revenue? Predict the key drivers.",
    "Compare online vs retail vs partner channel revenue by region.",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Always (re)seed on startup so the sample data spans up to the current date.
    db = Database()
    log.info("Seeding sample warehouse on startup")
    seed_database(db)
    yield


app = FastAPI(title="Autonomous Data Scientist API", version="1.0.0", lifespan=lifespan)

# Allow the static frontend (GitHub Pages / localhost) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> dict:
    db = Database()
    return {"ok": True, "seeded": db.exists() and bool(db.list_tables())}


@app.get("/examples")
def examples() -> dict:
    return {"examples": EXAMPLES}


@app.get("/diag")
def diag() -> dict:
    """Diagnostics: is the LLM reachable? Never returns the key itself."""
    import os

    from config.settings import get_settings

    s = get_settings()
    info = {
        "provider": s.llm_provider,
        "model": s.llm_model,
        "google_api_key_env_present": bool(os.getenv("GOOGLE_API_KEY")),
        "active_api_key_present": bool(s.active_api_key),
    }
    try:
        from ads.llm.client import get_llm_client

        resp = get_llm_client().complete("Reply with: OK", system="diagnostic")
        info["llm_call"] = "ok"
        info["llm_reply"] = (resp.text or "")[:40]
    except Exception as exc:  # noqa: BLE001
        info["llm_call"] = "failed"
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def _charts_as_data_urls(paths: list[str]) -> list[str]:
    out: list[str] = []
    for c in paths or []:
        p = Path(c)
        if p.exists():
            out.append("data:image/png;base64," + base64.b64encode(p.read_bytes()).decode())
    return out


@app.post("/run")
def run(req: RunRequest) -> dict:
    from ads.core.exceptions import RateLimitError

    try:
        result = run_workflow(req.question)
    except RateLimitError as exc:
        when = f" Try again in about {exc.retry_after}." if exc.retry_after else " Please try again later."
        window_word = {"day": "daily", "hour": "hourly", "minute": "per-minute"}.get(exc.window or "", "")
        window = f" (the {window_word} free AI limit was reached)" if window_word else ""
        log.warning("Rate limited: %s", exc.details)
        return {
            "status": "rate_limited",
            "message": f"The AI usage limit has been reached{window}.{when}",
            "retry_after": exc.retry_after,
            "window": exc.window,
            "question": req.question,
        }
    except Exception as exc:  # noqa: BLE001 - surface the real cause to the client
        log.exception("Run failed")
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}", "question": req.question}
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
