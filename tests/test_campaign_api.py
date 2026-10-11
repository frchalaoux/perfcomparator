from __future__ import annotations

import time
from threading import Event

from fastapi.testclient import TestClient
from test_repository import sample_report

from perfcomparator import app as app_module
from perfcomparator.apis.v1 import campaigns as campaigns_api
from perfcomparator.app import create_app
from perfcomparator.core.config import Settings
from perfcomparator.models import CampaignRequest, ProcessLoad, ReadinessSnapshot

API_TOKEN = "secret"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Idempotency-Key": "campaign-0001",
}
BODY = {
    "profile": "quick",
    "benchmark_ids": ["cpu.integer"],
    "repetitions": 1,
    "label": "API test",
}


def _wait_for_status(client: TestClient, task_id: str, expected: str) -> dict:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        response = client.get(
            f"/api/v1/jobs/{task_id}",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
        assert response.status_code == 200
        task = response.json()
        if task["status"] == expected:
            return task
        if task["status"] in {"failed", "interrupted"}:
            break
        time.sleep(0.01)
    raise AssertionError(f"La tâche n'a pas atteint l'état {expected}.")


def test_campaign_routes_create_replay_read_and_stream_events(monkeypatch, tmp_path) -> None:
    report = sample_report(label="API test")

    class FakeExecutor:
        def __init__(self, **_kwargs):
            pass

        def execute(self, request, *, progress=None, should_cancel=None):
            assert request == CampaignRequest.model_validate(BODY)
            if progress:
                progress("cpu.integer", None)
                progress("cpu.integer", report.results[0])
            return report

    monkeypatch.setattr(app_module, "LocalBenchmarkExecutor", FakeExecutor)
    app = create_app(
        Settings(
            api_token=API_TOKEN,
            state_dir=tmp_path / "state",
            reports_dir=tmp_path / "reports",
        )
    )
    with TestClient(app, base_url="http://127.0.0.1") as client:
        unauthorized = client.post("/api/v1/runs", json=BODY)
        created = client.post("/api/v1/runs", json=BODY, headers=HEADERS)
        replay = client.post("/api/v1/runs", json=BODY, headers=HEADERS)

        assert unauthorized.status_code == 401
        assert created.status_code == 202
        assert replay.status_code == 200
        assert replay.json()["created"] is False
        task_id = created.json()["task"]["task_id"]
        task = _wait_for_status(client, task_id, "succeeded")
        events = client.get(
            f"/api/v1/jobs/{task_id}/events",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
        resumed_events = client.get(
            f"/api/v1/jobs/{task_id}/events",
            headers={
                "Authorization": f"Bearer {API_TOKEN}",
                "Last-Event-ID": "3",
            },
        )
        conflicting_replay = client.post(
            "/api/v1/runs",
            json={**BODY, "label": "Autre demande"},
            headers=HEADERS,
        )
        missing = client.get(
            "/api/v1/jobs/missing",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )

    assert task["completed_benchmarks"] == 1
    assert task["report_id"].startswith("sha256:")
    assert events.status_code == 200
    assert events.headers["content-type"].startswith("text/event-stream")
    assert "event: benchmark_succeeded" in events.text
    assert "event: completed" in events.text
    assert "id: 5" in events.text
    assert "id: 3\n" not in resumed_events.text
    assert "id: 4\n" in resumed_events.text
    assert "id: 5\n" in resumed_events.text
    assert conflicting_replay.status_code == 409
    assert conflicting_replay.json()["error"]["code"] == "idempotency_conflict"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_readiness_route_returns_preflight_summary_without_pid(monkeypatch, tmp_path) -> None:
    snapshot = ReadinessSnapshot(
        sample_seconds=1,
        cpu_percent=5,
        memory_available_percent=60,
        memory_available_bytes=6_000_000,
        swap_percent=0,
        active_processes=[ProcessLoad(pid=1234, name="editor", cpu_percent=3, memory_percent=4)],
        warnings=["Processus actifs détectés : editor."],
        suitable=False,
    )
    monkeypatch.setattr(campaigns_api, "machine_readiness", lambda: snapshot)
    app = create_app(
        Settings(
            api_token=API_TOKEN,
            state_dir=tmp_path / "state",
            reports_dir=tmp_path / "reports",
        )
    )
    with TestClient(app, base_url="http://127.0.0.1") as client:
        response = client.post(
            "/api/v1/readiness",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )

    assert response.status_code == 200
    assert response.json()["cpu_percent"] == 5
    assert response.json()["warnings"] == ["Processus actifs détectés : editor."]
    assert response.json()["active_processes"] == [
        {"name": "editor", "cpu_percent": 3, "memory_percent": 4}
    ]
    assert "pid" not in response.text
    assert app.state.task_store.active() is None


def test_campaign_routes_report_engine_busy_and_allow_cooperative_cancel(
    monkeypatch, tmp_path
) -> None:
    started = Event()

    class BlockingExecutor:
        def __init__(self, **_kwargs):
            pass

        def execute(self, _request, *, progress=None, should_cancel=None):
            started.set()
            while not should_cancel():
                time.sleep(0.005)
            return sample_report().model_copy(update={"execution_status": "cancelled"})

    monkeypatch.setattr(app_module, "LocalBenchmarkExecutor", BlockingExecutor)
    monkeypatch.setattr(
        campaigns_api,
        "machine_readiness",
        lambda: (_ for _ in ()).throw(AssertionError("readiness must not run during a campaign")),
    )
    app = create_app(
        Settings(
            api_token=API_TOKEN,
            state_dir=tmp_path / "state",
            reports_dir=tmp_path / "reports",
        )
    )
    with TestClient(app, base_url="http://127.0.0.1") as client:
        created = client.post("/api/v1/runs", json=BODY, headers=HEADERS)
        task_id = created.json()["task"]["task_id"]
        assert started.wait(timeout=2)

        busy = client.post(
            "/api/v1/runs",
            json=BODY,
            headers={**HEADERS, "Idempotency-Key": "campaign-0002"},
        )
        readiness_busy = client.post(
            "/api/v1/readiness",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
        cancel = client.post(
            f"/api/v1/jobs/{task_id}/cancel",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )
        task = _wait_for_status(client, task_id, "cancelled")
        already_done = client.post(
            f"/api/v1/jobs/{task_id}/cancel",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )

    assert busy.status_code == 409
    assert busy.json()["error"]["code"] == "engine_busy"
    assert busy.json()["active_task"]["task_id"] == task_id
    assert readiness_busy.status_code == 409
    assert readiness_busy.json()["error"]["code"] == "engine_busy"
    assert cancel.status_code == 202
    assert cancel.json()["cancellation_requested"] is True
    assert task["status"] == "cancelled"
    assert already_done.status_code == 200
    assert already_done.json()["cancellation_requested"] is False
