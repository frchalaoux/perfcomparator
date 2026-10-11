"""Authentification partagée des routes de l’API locale PCE."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, Request


def require_api_token(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    token = request.app.state.settings.api_token
    expected = f"Bearer {token}" if token else ""
    if not expected or not secrets.compare_digest(authorization or "", expected):
        raise HTTPException(status_code=401, detail="unauthorized")
