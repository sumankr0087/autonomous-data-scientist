"""Metadata routes: health, examples, providers and diagnostics."""

from __future__ import annotations

from fastapi import APIRouter

from ads.api.catalog import EXAMPLES, PROVIDER_CATALOG
from ads.core.logging import get_logger
from ads.tools.database import Database

log = get_logger(__name__)
router = APIRouter()


@router.get("/health")
def health() -> dict:
    db = Database()
    return {"ok": True, "seeded": db.exists() and bool(db.list_tables())}


@router.get("/examples")
def examples() -> dict:
    return {"examples": EXAMPLES}


@router.get("/providers")
def providers() -> dict:
    """List model options that actually have a key configured on the server."""
    from config.settings import get_settings

    s = get_settings()
    available = [
        {"provider": p["id"], "model": p["model"], "label": p["label"]}
        for p in PROVIDER_CATALOG
        if s.key_for(p["id"])
    ]
    return {"providers": available, "default_provider": s.llm_provider, "default_model": s.llm_model}


@router.get("/diag")
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
