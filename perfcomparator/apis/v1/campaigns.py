"""Routes de création, suivi et annulation des campagnes."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from perfcomparator.apis.security import require_api_token
from perfcomparator.models import CampaignRequest
from perfcomparator.system_info import machine_readiness
from perfcomparator.tasks import (
    CampaignOrchestrator,
    CampaignTask,
    EngineBusy,
    IdempotencyConflict,
    TaskNotFound,
)

from .schemas import (
    CampaignCancellationResponse,
    CampaignEventResponse,
    CampaignReadinessResponse,
    CampaignSubmissionResponse,
    CampaignTaskResponse,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["campaigns"],
    dependencies=[Depends(require_api_token)],
)
TERMINAL_STATUSES = {
    "succeeded",
    "completed_with_errors",
    "failed",
    "cancelled",
    "interrupted",
}


def _orchestrator(request: Request) -> CampaignOrchestrator:
    return request.app.state.campaigns


def _busy_response(task: CampaignTask) -> JSONResponse:
    request_id = uuid.uuid4().hex
    response = {
        "error": {
            "code": "engine_busy",
            "message": "Une autre campagne utilise déjà le moteur.",
            "request_id": request_id,
        },
        "active_task": CampaignTaskResponse.from_task(task).model_dump(mode="json"),
    }
    return JSONResponse(
        status_code=409,
        content=response,
        headers={"X-Request-ID": request_id},
    )


@router.post("/readiness", response_model=CampaignReadinessResponse)
def check_campaign_readiness(request: Request) -> CampaignReadinessResponse | JSONResponse:
    try:
        snapshot = _orchestrator(request).check_readiness(machine_readiness)
    except EngineBusy as error:
        return _busy_response(error.task)
    return CampaignReadinessResponse.from_snapshot(snapshot)


@router.post(
    "/runs",
    response_model=CampaignSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_campaign(
    campaign_request: CampaignRequest,
    request: Request,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=200,
        pattern=r"^[A-Za-z0-9._:-]+$",
    ),
) -> CampaignSubmissionResponse | JSONResponse:
    try:
        task, created = _orchestrator(request).submit(campaign_request, idempotency_key)
    except IdempotencyConflict as error:
        raise HTTPException(status_code=409, detail="idempotency_conflict") from error
    except EngineBusy as error:
        return _busy_response(error.task)

    submission = CampaignSubmissionResponse(
        task=CampaignTaskResponse.from_task(task),
        created=created,
    )
    if created:
        return submission
    return JSONResponse(status_code=200, content=submission.model_dump(mode="json"))


@router.get("/jobs/{task_id}", response_model=CampaignTaskResponse)
def get_campaign(task_id: str, request: Request) -> CampaignTaskResponse:
    try:
        return CampaignTaskResponse.from_task(_orchestrator(request).get(task_id))
    except TaskNotFound as error:
        raise HTTPException(status_code=404, detail="task_not_found") from error


@router.post(
    "/jobs/{task_id}/cancel",
    response_model=CampaignCancellationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def cancel_campaign(
    task_id: str,
    request: Request,
) -> CampaignCancellationResponse | JSONResponse:
    try:
        task, accepted = _orchestrator(request).cancel(task_id)
    except TaskNotFound as error:
        raise HTTPException(status_code=404, detail="task_not_found") from error
    response = CampaignCancellationResponse(
        task=CampaignTaskResponse.from_task(task),
        cancellation_requested=accepted,
    )
    if accepted:
        return response
    return JSONResponse(status_code=200, content=response.model_dump(mode="json"))


@router.get("/jobs/{task_id}/events")
async def campaign_events(
    task_id: str,
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    after_sequence: int | None = Query(default=None, ge=0),
) -> StreamingResponse:
    orchestrator = _orchestrator(request)
    try:
        orchestrator.get(task_id)
    except TaskNotFound as error:
        raise HTTPException(status_code=404, detail="task_not_found") from error

    if last_event_id is not None:
        if not last_event_id.isascii() or not last_event_id.isdecimal():
            raise HTTPException(status_code=422, detail="invalid_event_id")
        cursor = int(last_event_id)
    else:
        cursor = after_sequence or 0

    async def stream() -> AsyncIterator[str]:
        nonlocal cursor
        last_heartbeat = time.monotonic()
        while not await request.is_disconnected():
            page = await asyncio.to_thread(orchestrator.event_page, task_id, after_sequence=cursor)
            if page.history_expired:
                payload = json.dumps(
                    {
                        "history_expired": True,
                        "latest_sequence": page.latest_sequence,
                    },
                    separators=(",", ":"),
                )
                yield f"id: {page.latest_sequence}\nevent: resync\ndata: {payload}\n\n"
                cursor = page.latest_sequence
                events = []
            else:
                events = page.events
            for event in events:
                payload = CampaignEventResponse.from_event(event).model_dump_json()
                yield f"id: {event.sequence}\nevent: {event.event_type}\ndata: {payload}\n\n"
                cursor = event.sequence

            task = await asyncio.to_thread(orchestrator.get, task_id)
            if task.status in TERMINAL_STATUSES and cursor >= page.latest_sequence:
                break
            if time.monotonic() - last_heartbeat >= 15:
                yield ": keep-alive\n\n"
                last_heartbeat = time.monotonic()
            await asyncio.sleep(0.25)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
