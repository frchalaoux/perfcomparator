"""Routes de santé de l’API PCE."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


@router.get("/health")
async def api_health(
    request: Request, authorization: str | None = Header(default=None)
) -> dict[str, str]:
    token = request.app.state.settings.api_token
    expected = f"Bearer {token}" if token else ""
    if not expected or not secrets.compare_digest(authorization or "", expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"status": "ok", "component": "pce", "api_version": "v1"}
