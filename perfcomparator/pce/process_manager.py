"""Démarrage et arrêt local du processus PCE."""

from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from platformdirs import user_state_path

STATE_DIR = Path(
    os.environ.get("PERFCOMPARATOR_STATE_DIR")
    or user_state_path("perfcomparator", appauthor=False)
)
STATE_FILE = STATE_DIR / "engine.json"


def _state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        STATE_DIR.chmod(0o700)
    return STATE_DIR


def _write_state(data: dict[str, object]) -> None:
    _state_dir()
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    if os.name != "nt":
        temporary.chmod(0o600)
    temporary.replace(STATE_FILE)


def read_state() -> dict[str, object] | None:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(url: str, token: str | None = None, *, post: bool = False) -> bytes:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, headers=headers, method="POST" if post else "GET")
    with urllib.request.urlopen(request, timeout=1.0) as response:
        return response.read()


def _terminate_failed_start(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except OSError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def _remove_state_for_process(pid: int) -> None:
    state = read_state()
    if state and state.get("pid") == pid:
        STATE_FILE.unlink(missing_ok=True)


def is_running() -> bool:
    state = read_state()
    if not state:
        return False
    try:
        payload = json.loads(
            _request(f"{state['url']}/api/v1/health", str(state["api_token"]))
        )
        return payload.get("component") == "pce"
    except (OSError, urllib.error.URLError, KeyError, ValueError):
        return False


def web_is_running() -> bool:
    try:
        web_state = json.loads((STATE_DIR / "web.json").read_text(encoding="utf-8"))
        payload = json.loads(_request(f"{web_state['url']}/health"))
        return payload.get("component") == "pcweb"
    except (OSError, json.JSONDecodeError, urllib.error.URLError, KeyError, ValueError):
        return False


def start() -> dict[str, object]:
    if is_running():
        return read_state() or {}
    state_dir = _state_dir()
    port = _free_port()
    api_token = secrets.token_urlsafe(32)
    control_token = secrets.token_urlsafe(32)
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(
        {
            "PERFCOMPARATOR_ENGINE_PORT": str(port),
            "PERFCOMPARATOR_ENGINE_TOKEN": api_token,
            "PERFCOMPARATOR_ENGINE_CONTROL_TOKEN": control_token,
        }
    )
    log_path = state_dir / "engine.log"
    with log_path.open("ab") as log_file:
        kwargs: dict[str, object] = {"stdout": log_file, "stderr": subprocess.STDOUT}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen(
            [sys.executable, "-m", "perfcomparator.pce.server"],
            stdin=subprocess.DEVNULL,
            env=env,
            close_fds=True,
            **kwargs,
        )
    state: dict[str, object] = {
        "pid": process.pid,
        "url": url,
        "api_token": api_token,
        "control_token": control_token,
        "log": str(log_path),
    }
    try:
        _write_state(state)
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"PCE s'est arrêté au démarrage. Consultez {log_path}.")
            try:
                payload = json.loads(_request(f"{url}/api/v1/health", api_token))
                if payload.get("component") == "pce":
                    return state
            except (OSError, urllib.error.URLError, ValueError):
                time.sleep(0.1)
        raise RuntimeError(f"PCE ne répond pas après 10 secondes. Consultez {log_path}.")
    except BaseException:
        _terminate_failed_start(process)
        _remove_state_for_process(process.pid)
        raise


def stop() -> bool:
    state = read_state()
    if not state:
        return False
    try:
        _request(
            f"{state['url']}/_control/shutdown",
            str(state["control_token"]),
            post=True,
        )
    except (OSError, urllib.error.URLError, KeyError):
        STATE_FILE.unlink(missing_ok=True)
        return False
    for _ in range(100):
        try:
            _request(f"{state['url']}/health")
        except (OSError, urllib.error.URLError, KeyError):
            STATE_FILE.unlink(missing_ok=True)
            return True
        time.sleep(0.1)
    raise RuntimeError("PCE ne s'est pas arrêté après la demande d'arrêt.")
