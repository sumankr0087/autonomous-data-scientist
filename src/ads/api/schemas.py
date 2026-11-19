"""Request/response schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel


class RunRequest(BaseModel):
    question: str
    provider: str | None = None
    model: str | None = None
