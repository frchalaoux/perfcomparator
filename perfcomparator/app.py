"""Fabrique FastAPI du serveur PCE."""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .apis.base import api_router
from .core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_environment()
    app = FastAPI(title="PerfComparator Engine", version="1")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.state.settings = resolved
    app.include_router(api_router)
    return app
