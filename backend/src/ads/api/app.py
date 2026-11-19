"""FastAPI application factory for the Autonomous Data Scientist.

Exposes the agent workflow as a JSON API so a static React/Next frontend can call
it. The LLM API key stays on this server (never in the browser).

Run locally:  uvicorn api:app --reload   (from the repo root)
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ads.api.routes.meta import router as meta_router
from ads.api.routes.run import router as run_router
from ads.core.logging import get_logger
from ads.data.seed import seed_database
from ads.tools.database import Database

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Always (re)seed on startup so the sample data spans up to the current date.
    db = Database()
    log.info("Seeding sample warehouse on startup")
    seed_database(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Autonomous Data Scientist API", version="1.0.0", lifespan=lifespan)

    # Allow the static frontend (GitHub Pages / localhost) to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta_router)
    app.include_router(run_router)
    return app


app = create_app()
