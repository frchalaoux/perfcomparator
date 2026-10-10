"""Fabrique FastAPI du serveur PCE."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .apis.base import api_router
from .core.config import Settings
from .executor import LocalBenchmarkExecutor
from .repository import JsonReportRepository
from .tasks import CampaignOrchestrator, CampaignTaskStore


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_environment()
    task_store = CampaignTaskStore(resolved.state_dir / "campaigns.sqlite3")
    reports = JsonReportRepository(resolved.reports_dir)
    campaigns = CampaignOrchestrator(
        task_store,
        reports,
        LocalBenchmarkExecutor(work_dir=resolved.state_dir / "work"),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            await asyncio.to_thread(campaigns.close)

    app = FastAPI(title="PerfComparator Engine", version="1", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.state.settings = resolved
    app.state.reports = reports
    app.state.task_store = task_store
    app.state.campaigns = campaigns

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        detail = error.detail if isinstance(error.detail, str) else ""
        known_errors = {
            "unauthorized": ("unauthorized", "Authentification requise."),
            "forbidden": ("forbidden", "Accès refusé."),
            "benchmark_not_found": ("not_found", "Cette ressource n’existe pas."),
            "report_not_found": ("not_found", "Cette ressource n’existe pas."),
            "task_not_found": ("not_found", "Cette ressource n’existe pas."),
            "idempotency_conflict": (
                "idempotency_conflict",
                "Cette clé a déjà été utilisée pour une autre demande.",
            ),
        }
        if error.status_code == 404:
            default_error = ("not_found", "Cette ressource n’existe pas.")
        elif error.status_code >= 500:
            default_error = ("internal_error", "Une erreur interne a empêché la requête.")
        else:
            default_error = ("request_rejected", "La requête n’a pas pu être traitée.")
        code, message = known_errors.get(detail, default_error)
        return _error_response(request, error.status_code, code, message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, _error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request, 422, "invalid_request", "Les paramètres de la requête sont invalides."
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _error: Exception) -> JSONResponse:
        return _error_response(
            request, 500, "internal_error", "Une erreur interne a empêché la requête."
        )

    app.include_router(api_router)
    return app


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = uuid.uuid4().hex
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )
