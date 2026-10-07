from fastapi.testclient import TestClient

from perfcomparator.pce.app import create_app
from perfcomparator.pce.config import Settings


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
