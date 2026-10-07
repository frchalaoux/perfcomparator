import urllib.error

import pytest

from perfcomparator.pce import process_manager


class _FakeProcess:
    pid = 48123

    def __init__(self) -> None:
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False
        self.waited = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        self.waited = True
        return self.returncode or 0


def test_failed_engine_start_terminates_process_and_removes_its_state(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_file = tmp_path / "engine.json"
    process = _FakeProcess()
    monkeypatch.setattr(process_manager, "STATE_DIR", tmp_path)
    monkeypatch.setattr(process_manager, "STATE_FILE", state_file)
    monkeypatch.setattr(process_manager, "_free_port", lambda: 8765)
    monkeypatch.setattr(process_manager.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(process_manager.time, "sleep", lambda _seconds: None)

    def unavailable(_url: str, _token: str | None = None, *, post: bool = False) -> bytes:
        raise urllib.error.URLError("not ready")

    monkeypatch.setattr(process_manager, "_request", unavailable)

    with pytest.raises(RuntimeError, match="PCE ne répond pas"):
        process_manager.start()

    assert process.terminated
    assert process.waited
    assert not process.killed
    assert not state_file.exists()
