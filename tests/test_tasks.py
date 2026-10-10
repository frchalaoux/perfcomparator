from __future__ import annotations

import time
from threading import Event

import pytest
from test_repository import sample_report

from perfcomparator.models import CampaignRequest
from perfcomparator.repository import JsonReportRepository
from perfcomparator.tasks import (
    CampaignOrchestrator,
    CampaignTaskStore,
    EngineBusy,
    IdempotencyConflict,
)


def _request(*, label: str | None = None) -> CampaignRequest:
    return CampaignRequest(
        profile="quick",
        benchmark_ids=["cpu.integer"],
        repetitions=1,
        label=label,
    )


def test_task_store_is_idempotent_and_allows_only_one_active_campaign(tmp_path) -> None:
    store = CampaignTaskStore(tmp_path / "campaigns.sqlite3")

    first, created = store.create(_request(), "request-0001")
    replay, replay_created = store.create(_request(), "request-0001")

    assert created
    assert not replay_created
    assert replay.task_id == first.task_id
    with pytest.raises(IdempotencyConflict):
        store.create(_request(label="different"), "request-0001")
    with pytest.raises(EngineBusy) as error:
        store.create(_request(), "request-0002")
    assert error.value.task.task_id == first.task_id


def test_task_event_page_reports_expired_history(tmp_path) -> None:
    store = CampaignTaskStore(tmp_path / "campaigns.sqlite3", max_events_per_task=2)
    task, _ = store.create(_request(), "request-0001")

    assert store.mark_running(task.task_id)
    store.record_progress(task.task_id, "cpu.integer", outcome="started")
    page = store.event_page(task.task_id, after_sequence=0)

    assert page.history_expired
    assert page.first_available_sequence == 2
    assert [event.sequence for event in page.events] == [2, 3]


def test_orchestrator_executes_and_persists_report_and_progress(tmp_path) -> None:
    report = sample_report(label="Campagne API")

    class FakeExecutor:
        def execute(self, request, *, progress=None, should_cancel=None):
            assert request == _request(label="Campagne API")
            assert should_cancel is not None
            if progress:
                progress("cpu.integer", None)
                progress("cpu.integer", report.results[0])
            return report

    store = CampaignTaskStore(tmp_path / "state" / "campaigns.sqlite3")
    reports = JsonReportRepository(tmp_path / "reports")
    orchestrator = CampaignOrchestrator(store, reports, FakeExecutor())
    try:
        task, created = orchestrator.submit(_request(label="Campagne API"), "request-0001")
        assert created

        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            task = orchestrator.get(task.task_id)
            if task.status in {"succeeded", "failed"}:
                break
            time.sleep(0.01)

        assert task.status == "succeeded"
        assert task.completed_benchmarks == 1
        assert task.report_id is not None
        events = orchestrator.events(task.task_id)
        assert [event.event_type for event in events] == [
            "accepted",
            "started",
            "benchmark_started",
            "benchmark_succeeded",
            "completed",
        ]
        assert reports.reports() == [report]
    finally:
        orchestrator.close()


def test_orchestrator_cooperatively_cancels_campaign(tmp_path) -> None:
    started = Event()

    class BlockingExecutor:
        def execute(self, request, *, progress=None, should_cancel=None):
            started.set()
            assert should_cancel is not None
            while not should_cancel():
                time.sleep(0.005)
            return sample_report().model_copy(update={"execution_status": "cancelled"})

    orchestrator = CampaignOrchestrator(
        CampaignTaskStore(tmp_path / "state" / "campaigns.sqlite3"),
        JsonReportRepository(tmp_path / "reports"),
        BlockingExecutor(),
    )
    try:
        task, _ = orchestrator.submit(_request(), "request-0001")
        assert started.wait(timeout=2)
        cancel_state, accepted = orchestrator.cancel(task.task_id)
        assert accepted
        assert cancel_state.status == "cancel_requested"

        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            task = orchestrator.get(task.task_id)
            if task.status in {"cancelled", "failed"}:
                break
            time.sleep(0.01)

        assert task.status == "cancelled"
        assert [event.event_type for event in orchestrator.events(task.task_id)][-2:] == [
            "cancel_requested",
            "cancelled",
        ]
    finally:
        orchestrator.close()
