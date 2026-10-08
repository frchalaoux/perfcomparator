"""Routes de contrôle interne du processus PCE."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


@router.post("/_control/shutdown", include_in_schema=False)
async def shutdown(
    request: Request, authorization: str | None = Header(default=None)
) -> dict[str, str]:
    token = request.app.state.settings.control_token
    expected = f"Bearer {token}" if token else ""
    if not expected or not secrets.compare_digest(authorization or "", expected):
        raise HTTPException(status_code=403, detail="forbidden")
    request.app.state.shutdown_requested = True
    return {"status": "stopping"}
