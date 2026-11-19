"""API package. Re-exports the FastAPI app so `from ads.api import app` works."""

from ads.api.app import app

__all__ = ["app"]
