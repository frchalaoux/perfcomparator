"""Fabrique FastAPI du serveur PCE."""

from __future__ import annotations

import secrets

from fastapi import FastAPI, Header, HTTPException, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_environment()
    app = FastAPI(title="PerfComparator Engine", version="1")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.state.settings = resolved

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "component": "pce"}

    @app.get("/api/v1/health")
    async def api_health(authorization: str | None = Header(default=None)) -> dict[str, str]:
        expected = f"Bearer {resolved.api_token}" if resolved.api_token else ""
        if not expected or not secrets.compare_digest(authorization or "", expected):
            raise HTTPException(status_code=401, detail="unauthorized")
        return {"status": "ok", "component": "pce", "api_version": "v1"}

    @app.post("/_control/shutdown", include_in_schema=False)
    async def shutdown(request: Request, authorization: str | None = Header(default=None)) -> dict[str, str]:
        expected = f"Bearer {resolved.control_token}" if resolved.control_token else ""
        if not expected or not secrets.compare_digest(authorization or "", expected):
            raise HTTPException(status_code=403, detail="forbidden")
        request.app.state.shutdown_requested = True
        return {"status": "stopping"}

    return app
