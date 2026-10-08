"""Assemblage des routes HTTP PCE."""

from fastapi import APIRouter

from .control import router as control_router
from .v1.health import router as health_router

api_router = APIRouter()


@api_router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok", "component": "pce"}


api_router.include_router(health_router, prefix="/api/v1", tags=["health"])
api_router.include_router(control_router)
