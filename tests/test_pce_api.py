import hashlib
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from perfcomparator.apis.v1 import resources
from perfcomparator.app import create_app
from perfcomparator.core.config import Settings
from perfcomparator.gpu_benchmarks import GpuAdapterSummary
from perfcomparator.models import BenchmarkReport, BenchmarkResult, SystemSnapshot
from perfcomparator.repository import JsonReportRepository

API_TOKEN = "secret"


def _client(reports_dir, *, token: str = API_TOKEN) -> TestClient:
    return TestClient(
        create_app(Settings(api_token=token, reports_dir=reports_dir)),
        base_url="http://127.0.0.1",
    )


def _sample_system() -> SystemSnapshot:
    return SystemSnapshot(
        system="Darwin",
        release="25.0",
        version="test",
        machine="arm64",
        model="Mac16,1",
        manufacturer="Apple",
        product_name="MacBook Pro",
        processor="Apple M4",
        physical_cpu_count=10,
        logical_cpu_count=10,
        memory_bytes=16 * 1_073_741_824,
        gpu_devices=["Apple M4"],
        python_version="3.14.4",
        python_implementation="CPython",
        python_executable="/private/user/python",
        disk_total_bytes=1_000_000,
        disk_free_bytes=500_000,
    )


def _sample_report() -> BenchmarkReport:
    return BenchmarkReport(
        suite_version="0.5.0",
        protocol_version="0.3.0",
        recorded_at=datetime(2026, 10, 1, 12, tzinfo=UTC),
        label="Machine de test",
        profile="quick",
        repetitions=2,
        requested_benchmarks=["cpu.integer"],
        system=_sample_system(),
        results=[
            BenchmarkResult(
                benchmark_id="cpu.integer",
                group="cpu",
                name="Entiers mono-cœur",
                description="Charge entière de test.",
                value=10.5,
                unit="Mop/s",
                elapsed_seconds=1.0,
                repetitions=2,
                sample_values=[10.0, 11.0],
                minimum=10.0,
                maximum=11.0,
                relative_spread_percent=100 / 10.5,
            )
        ],
    )


def test_engine_health_requires_the_local_api_token() -> None:
    with TestClient(
        create_app(Settings(api_token="secret", control_token="admin")),
        base_url="http://127.0.0.1",
    ) as client:
        assert client.get("/api/v1/health").status_code == 401
        response = client.get("/api/v1/health", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "component": "pce", "api_version": "v1"}


def test_shutdown_requires_the_private_control_token() -> None:
    with TestClient(
        create_app(Settings(api_token="secret", control_token="admin")),
        base_url="http://127.0.0.1",
    ) as client:
        assert client.post("/_control/shutdown").status_code == 403
        response = client.post(
            "/_control/shutdown",
            headers={"Authorization": "Bearer admin"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "stopping"}


def test_engine_rejects_an_untrusted_host() -> None:
    with TestClient(
        create_app(Settings(api_token="secret", control_token="admin")),
        base_url="http://127.0.0.1",
    ) as client:
        response = client.get("/health", headers={"host": "example.com"})

    assert response.status_code == 400


def test_read_only_routes_require_the_api_token(tmp_path) -> None:
    with _client(tmp_path) as client:
        response = client.get("/api/v1/system")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["x-request-id"] == response.json()["error"]["request_id"]


def test_system_route_filters_private_python_path_and_returns_gpu_adapters(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(resources, "system_snapshot", lambda _path: _sample_system())
    monkeypatch.setattr(
        resources,
        "gpu_adapters",
        lambda: (GpuAdapterSummary(0, "Apple M4", "Metal", "integratedgpu"),),
    )

    with _client(tmp_path) as client:
        response = client.get(
            "/api/v1/system", headers={"Authorization": f"Bearer {API_TOKEN}"}
        )

    assert response.status_code == 200
    assert response.json()["system"]["product_name"] == "MacBook Pro"
    assert response.json()["gpu_adapters"] == [
        {"index": 0, "device": "Apple M4", "backend": "Metal", "adapter_type": "integratedgpu"}
    ]
    assert "python_executable" not in response.json()["system"]
    assert "/private/user/python" not in response.text


def test_system_route_keeps_inventory_available_when_gpu_detection_fails(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(resources, "system_snapshot", lambda _path: _sample_system())

    def fail_gpu_detection():
        raise RuntimeError("driver detail must not escape")

    monkeypatch.setattr(resources, "gpu_adapters", fail_gpu_detection)

    with _client(tmp_path) as client:
        response = client.get(
            "/api/v1/system", headers={"Authorization": f"Bearer {API_TOKEN}"}
        )

    assert response.status_code == 200
    assert response.json()["gpu_adapters"] == []
    assert response.json()["warnings"] == ["L’inventaire des adaptateurs WebGPU est indisponible."]
    assert "driver detail must not escape" not in response.text


def test_benchmark_catalog_and_detail_use_catalog_metadata(tmp_path) -> None:
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    with _client(tmp_path) as client:
        catalog_response = client.get("/api/v1/benchmarks", headers=headers)
        detail_response = client.get("/api/v1/benchmarks/cpu.integer", headers=headers)

    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert "cpu.integer" in {item["benchmark_id"] for item in catalog["benchmarks"]}
    assert catalog["profiles"]
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["benchmark_id"] == "cpu.integer"
    assert detail["unit"] == "Mop/s"
    assert detail["methodology"]
    assert detail["references"]


def test_unknown_benchmark_returns_safe_not_found_envelope(tmp_path) -> None:
    with _client(tmp_path) as client:
        response = client.get(
            "/api/v1/benchmarks/cpu.unknown",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.headers["x-request-id"] == response.json()["error"]["request_id"]


def test_report_routes_paginate_warn_on_invalid_archives_and_filter_private_path(
    tmp_path,
) -> None:
    repository = JsonReportRepository(tmp_path)
    report_path = repository.save(_sample_report())
    (tmp_path / "benchmark_invalid.json").write_text("{invalid", encoding="utf-8")
    report_bytes = report_path.read_bytes()
    report_id = f"sha256:{hashlib.sha256(report_bytes).hexdigest()}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    with _client(tmp_path) as client:
        page_response = client.get("/api/v1/reports?offset=0&limit=1", headers=headers)
        detail_response = client.get(f"/api/v1/reports/{report_id}", headers=headers)

    assert page_response.status_code == 200
    page = page_response.json()
    assert page["total"] == 1
    assert page["offset"] == 0
    assert page["limit"] == 1
    assert page["reports"][0]["report_id"] == report_id
    assert page["warnings"] == ["Des archives JSON illisibles ont été ignorées."]
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["results"][0]["unit"] == "Mop/s"
    assert "python_executable" not in detail["system"]
    assert "/private/user/python" not in detail_response.text


def test_invalid_report_id_and_pagination_return_safe_errors(tmp_path) -> None:
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    with _client(tmp_path) as client:
        missing = client.get("/api/v1/reports/not-a-hash", headers=headers)
        invalid_limit = client.get("/api/v1/reports?limit=101", headers=headers)

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"
    assert invalid_limit.status_code == 422
    assert invalid_limit.json()["error"]["code"] == "invalid_request"
    assert invalid_limit.headers["x-request-id"] == invalid_limit.json()["error"]["request_id"]
