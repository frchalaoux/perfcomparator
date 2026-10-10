"""Persistance SQLite et orchestration mono-campagne du moteur local."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .executor import BenchmarkExecutor, LocalBenchmarkExecutor
from .models import (
    BenchmarkFailure,
    BenchmarkReport,
    BenchmarkResult,
    CampaignRequest,
    ReadinessSnapshot,
)
from .repository import JsonReportRepository

TaskStatus = Literal[
    "queued",
    "running",
    "cancel_requested",
    "succeeded",
    "completed_with_errors",
    "failed",
    "cancelled",
    "interrupted",
]
TaskEventType = Literal[
    "accepted",
    "started",
    "benchmark_started",
    "benchmark_succeeded",
    "benchmark_failed",
    "cancel_requested",
    "cancellation_result",
    "completed",
    "cancelled",
    "failed",
    "interrupted",
]
ACTIVE_STATUSES = ("queued", "running", "cancel_requested")
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,200}$")
MAX_EVENT_BYTES = 16 * 1024
MAX_EVENTS_PER_TASK = 1_000
EVENT_RETENTION = timedelta(days=30)


class CampaignTask(BaseModel):
    """État courant d'une tâche, sans chemin de fichier ni détail d'hôte."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    request: CampaignRequest
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    current_benchmark: str | None = None
    completed_benchmarks: int = Field(ge=0)
    total_benchmarks: int = Field(gt=0)
    report_id: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    error_code: str | None = Field(default=None, max_length=64)


class CampaignTaskEvent(BaseModel):
    """Événement de progression structuré, borné et séquencé par tâche."""

    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(gt=0)
    occurred_at: datetime
    event_type: TaskEventType
    payload: dict[str, str | int | float | bool | None]


class CampaignTaskEventPage(BaseModel):
    """Fenêtre d'événements et indication explicite d'un historique tronqué."""

    events: list[CampaignTaskEvent]
    first_available_sequence: int | None = None
    latest_sequence: int = Field(ge=0)
    history_expired: bool = False


class IdempotencyConflict(ValueError):
    """Une clé d'idempotence déjà utilisée porte un contenu différent."""


class EngineBusy(RuntimeError):
    """Une autre campagne utilise déjà le moteur matériel."""

    def __init__(self, task: CampaignTask) -> None:
        self.task = task
        super().__init__("Une campagne utilise déjà le moteur PerfComparator.")


class TaskNotFound(LookupError):
    """La tâche demandée n'existe pas."""


class CampaignTaskStore:
    """Stocke l'état des tâches et leurs événements dans une base SQLite locale."""

    def __init__(
        self,
        path: Path | str,
        *,
        event_retention: timedelta = EVENT_RETENTION,
        max_events_per_task: int = MAX_EVENTS_PER_TASK,
    ) -> None:
        if event_retention <= timedelta(0):
            raise ValueError("La durée de conservation des événements doit être positive.")
        if not 1 <= max_events_per_task <= MAX_EVENTS_PER_TASK:
            raise ValueError(f"Le plafond est compris entre 1 et {MAX_EVENTS_PER_TASK} événements.")
        self.path = Path(path).expanduser()
        self.event_retention = event_retention
        self.max_events_per_task = max_events_per_task
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            self.path.parent.chmod(0o700)
        with closing(self._connect()) as connection:
            schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
            if schema_version not in {0, 1}:
                raise RuntimeError(
                    f"Version de base des tâches non prise en charge : {schema_version}."
                )
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS campaign_tasks (
                    task_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    request_hash TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    current_benchmark TEXT,
                    completed_benchmarks INTEGER NOT NULL DEFAULT 0,
                    total_benchmarks INTEGER NOT NULL,
                    report_id TEXT,
                    error_code TEXT,
                    event_sequence INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS campaign_tasks_status_created
                    ON campaign_tasks(status, created_at);
                CREATE TABLE IF NOT EXISTS campaign_events (
                    task_id TEXT NOT NULL REFERENCES campaign_tasks(task_id) ON DELETE CASCADE,
                    sequence INTEGER NOT NULL,
                    occurred_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(task_id, sequence)
                );
                CREATE INDEX IF NOT EXISTS campaign_events_occurred
                    ON campaign_events(occurred_at);
                """
            )
            if schema_version == 0:
                connection.execute("PRAGMA user_version=1")
        if os.name != "nt":
            self.path.chmod(0o600)
        with self._transaction() as connection:
            self._prune_events(connection, self._now())

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _request_json(request: CampaignRequest) -> str:
        return json.dumps(
            request.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> CampaignTask:
        return CampaignTask(
            task_id=row["task_id"],
            request=CampaignRequest.model_validate_json(row["request_json"]),
            status=row["status"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            current_benchmark=row["current_benchmark"],
            completed_benchmarks=row["completed_benchmarks"],
            total_benchmarks=row["total_benchmarks"],
            report_id=row["report_id"],
            error_code=row["error_code"],
        )

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        task_id: str,
        event_type: TaskEventType,
        payload: dict[str, str | int | float | bool | None],
        *,
        now: datetime,
    ) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > MAX_EVENT_BYTES:
            raise ValueError("La charge de l'événement dépasse la taille autorisée.")
        connection.execute(
            "UPDATE campaign_tasks SET event_sequence=event_sequence+1 WHERE task_id=?",
            (task_id,),
        )
        sequence = connection.execute(
            "SELECT event_sequence FROM campaign_tasks WHERE task_id=?", (task_id,)
        ).fetchone()[0]
        connection.execute(
            """INSERT INTO campaign_events
               (task_id, sequence, occurred_at, event_type, payload_json)
               VALUES (?, ?, ?, ?, ?)""",
            (task_id, sequence, now.isoformat(), event_type, encoded),
        )

    def _prune_events(self, connection: sqlite3.Connection, now: datetime) -> None:
        cutoff = (now - self.event_retention).isoformat()
        connection.execute("DELETE FROM campaign_events WHERE occurred_at < ?", (cutoff,))
        connection.execute(
            """DELETE FROM campaign_events
               WHERE sequence NOT IN (
                   SELECT sequence FROM campaign_events AS retained
                   WHERE retained.task_id=campaign_events.task_id
                   ORDER BY sequence DESC LIMIT ?
               )""",
            (self.max_events_per_task,),
        )

    def create(self, request: CampaignRequest, idempotency_key: str) -> tuple[CampaignTask, bool]:
        """Crée une tâche, renvoie une reprise idempotente ou refuse si le moteur est occupé."""
        if IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key) is None:
            raise ValueError("La clé d'idempotence doit contenir de 8 à 200 caractères valides.")
        request_json = self._request_json(request)
        request_hash = hashlib.sha256(request_json.encode("utf-8")).hexdigest()
        now = self._now()
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM campaign_tasks WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise IdempotencyConflict(
                        "Cette clé d'idempotence a déjà servi pour une autre demande."
                    )
                return self._task_from_row(existing), False

            active = connection.execute(
                "SELECT * FROM campaign_tasks WHERE status IN (?, ?, ?) ORDER BY created_at LIMIT 1",
                ACTIVE_STATUSES,
            ).fetchone()
            if active is not None:
                raise EngineBusy(self._task_from_row(active))

            task_id = uuid.uuid4().hex
            connection.execute(
                """INSERT INTO campaign_tasks
                   (task_id, idempotency_key, request_hash, request_json, status,
                    created_at, total_benchmarks)
                   VALUES (?, ?, ?, ?, 'queued', ?, ?)""",
                (
                    task_id,
                    idempotency_key,
                    request_hash,
                    request_json,
                    now.isoformat(),
                    len(request.benchmark_ids),
                ),
            )
            self._append_event(connection, task_id, "accepted", {"status": "queued"}, now=now)
            self._prune_events(connection, now)
            row = connection.execute(
                "SELECT * FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            return self._task_from_row(row), True

    def get(self, task_id: str) -> CampaignTask:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if row is None:
            raise TaskNotFound(task_id)
        return self._task_from_row(row)

    def active(self) -> CampaignTask | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM campaign_tasks WHERE status IN (?, ?, ?) ORDER BY created_at LIMIT 1",
                ACTIVE_STATUSES,
            ).fetchone()
        return self._task_from_row(row) if row is not None else None

    def events(
        self, task_id: str, *, after_sequence: int = 0, limit: int = MAX_EVENTS_PER_TASK
    ) -> list[CampaignTaskEvent]:
        return self.event_page(task_id, after_sequence=after_sequence, limit=limit).events

    def event_page(
        self, task_id: str, *, after_sequence: int = 0, limit: int = MAX_EVENTS_PER_TASK
    ) -> CampaignTaskEventPage:
        if after_sequence < 0 or not 1 <= limit <= MAX_EVENTS_PER_TASK:
            raise ValueError("Séquence ou limite d'événements invalide.")
        with closing(self._connect()) as connection:
            connection.execute("BEGIN")
            task = connection.execute(
                "SELECT event_sequence FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if task is None:
                raise TaskNotFound(task_id)
            first = connection.execute(
                "SELECT MIN(sequence) FROM campaign_events WHERE task_id=?", (task_id,)
            ).fetchone()[0]
            rows = connection.execute(
                """SELECT sequence, occurred_at, event_type, payload_json
                   FROM campaign_events WHERE task_id=? AND sequence>?
                   ORDER BY sequence LIMIT ?""",
                (task_id, after_sequence, limit),
            ).fetchall()
        events = [
            CampaignTaskEvent(
                sequence=row["sequence"],
                occurred_at=row["occurred_at"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
            )
            for row in rows
        ]
        history_expired = task["event_sequence"] > after_sequence and (
            first is None or after_sequence < first - 1
        )
        return CampaignTaskEventPage(
            events=events,
            first_available_sequence=first,
            latest_sequence=task["event_sequence"],
            history_expired=history_expired,
        )

    def mark_running(self, task_id: str) -> bool:
        now = self._now()
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT status FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskNotFound(task_id)
            if row["status"] not in {"queued", "cancel_requested"}:
                return False
            connection.execute(
                """UPDATE campaign_tasks SET status=?, started_at=COALESCE(started_at, ?)
                   WHERE task_id=?""",
                (
                    row["status"] if row["status"] == "cancel_requested" else "running",
                    now.isoformat(),
                    task_id,
                ),
            )
            self._append_event(connection, task_id, "started", {}, now=now)
            self._prune_events(connection, now)
            return True

    def record_progress(
        self,
        task_id: str,
        benchmark_id: str,
        *,
        outcome: Literal["started", "succeeded", "failed"],
        result: BenchmarkResult | BenchmarkFailure | None = None,
    ) -> None:
        now = self._now()
        event_type: TaskEventType = {
            "started": "benchmark_started",
            "succeeded": "benchmark_succeeded",
            "failed": "benchmark_failed",
        }[outcome]
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT status, completed_benchmarks FROM campaign_tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if row is None:
                raise TaskNotFound(task_id)
            if row["status"] not in {"running", "cancel_requested"}:
                return
            completed = row["completed_benchmarks"] + int(outcome in {"succeeded", "failed"})
            current = benchmark_id if outcome == "started" else None
            connection.execute(
                """UPDATE campaign_tasks
                   SET current_benchmark=?, completed_benchmarks=? WHERE task_id=?""",
                (current, completed, task_id),
            )
            payload: dict[str, str | int | float | bool | None] = {
                "benchmark_id": benchmark_id,
                "completed": completed,
            }
            if isinstance(result, BenchmarkResult):
                payload.update(
                    value=result.value,
                    unit=result.unit,
                    repetitions=result.repetitions,
                )
            elif isinstance(result, BenchmarkFailure):
                payload["error_code"] = "benchmark_failed"
            self._append_event(
                connection,
                task_id,
                event_type,
                payload,
                now=now,
            )
            self._prune_events(connection, now)

    def request_cancel(self, task_id: str) -> tuple[CampaignTask, bool]:
        now = self._now()
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT status FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskNotFound(task_id)
            requested = row["status"] in {"queued", "running"}
            if requested:
                connection.execute(
                    "UPDATE campaign_tasks SET status='cancel_requested' WHERE task_id=?",
                    (task_id,),
                )
                self._append_event(
                    connection,
                    task_id,
                    "cancel_requested",
                    {"status": "cancel_requested"},
                    now=now,
                )
                self._prune_events(connection, now)
            updated = connection.execute(
                "SELECT * FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            return self._task_from_row(updated), requested or row["status"] == "cancel_requested"

    def finish(
        self,
        task_id: str,
        *,
        report_id: str,
        execution_status: Literal["completed", "cancelled"],
        has_failures: bool,
    ) -> CampaignTask:
        now = self._now()
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT status FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskNotFound(task_id)
            if row["status"] not in {"running", "cancel_requested"}:
                raise RuntimeError("La tâche n'est pas dans un état exécutable.")
            cancelled = execution_status == "cancelled"
            if row["status"] == "cancel_requested" and not cancelled:
                self._append_event(
                    connection,
                    task_id,
                    "cancellation_result",
                    {"cancelled": False},
                    now=now,
                )
            status: TaskStatus = (
                "cancelled"
                if cancelled
                else "completed_with_errors"
                if has_failures
                else "succeeded"
            )
            event_type: TaskEventType = "cancelled" if cancelled else "completed"
            connection.execute(
                """UPDATE campaign_tasks
                   SET status=?, finished_at=?, current_benchmark=NULL, report_id=?
                   WHERE task_id=?""",
                (status, now.isoformat(), report_id, task_id),
            )
            self._append_event(
                connection,
                task_id,
                event_type,
                {"status": status, "report_id": report_id},
                now=now,
            )
            self._prune_events(connection, now)
            updated = connection.execute(
                "SELECT * FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            return self._task_from_row(updated)

    def fail(self, task_id: str, *, error_code: str = "execution_failed") -> CampaignTask:
        now = self._now()
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT status FROM campaign_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskNotFound(task_id)
            if row["status"] not in ACTIVE_STATUSES:
                return self._task_from_row(
                    connection.execute(
                        "SELECT * FROM campaign_tasks WHERE task_id=?", (task_id,)
                    ).fetchone()
                )
            connection.execute(
                """UPDATE campaign_tasks SET status='failed', finished_at=?,
                   current_benchmark=NULL, error_code=? WHERE task_id=?""",
                (now.isoformat(), error_code, task_id),
            )
            self._append_event(
                connection,
                task_id,
                "failed",
                {"status": "failed", "error_code": error_code},
                now=now,
            )
            self._prune_events(connection, now)
            return self._task_from_row(
                connection.execute(
                    "SELECT * FROM campaign_tasks WHERE task_id=?", (task_id,)
                ).fetchone()
            )

    def recover_interrupted(self) -> list[str]:
        """Marque comme interrompues les tâches actives laissées par un arrêt brutal."""
        now = self._now()
        interrupted: list[str] = []
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT task_id FROM campaign_tasks WHERE status IN (?, ?, ?)",
                ACTIVE_STATUSES,
            ).fetchall()
            for row in rows:
                task_id = row["task_id"]
                connection.execute(
                    """UPDATE campaign_tasks SET status='interrupted', finished_at=?,
                       current_benchmark=NULL, error_code='process_interrupted'
                       WHERE task_id=?""",
                    (now.isoformat(), task_id),
                )
                self._append_event(
                    connection,
                    task_id,
                    "interrupted",
                    {"status": "interrupted", "error_code": "process_interrupted"},
                    now=now,
                )
                interrupted.append(task_id)
            self._prune_events(connection, now)
        return interrupted


class CampaignOrchestrator:
    """Lance une tâche à la fois et persiste état, progression et rapport."""

    def __init__(
        self,
        store: CampaignTaskStore,
        reports: JsonReportRepository,
        executor: BenchmarkExecutor | None = None,
    ) -> None:
        self.store = store
        self.reports = reports
        self.executor = executor if executor is not None else LocalBenchmarkExecutor()
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pce-campaign")
        self._lock = threading.Lock()
        self._cancel_events: dict[str, threading.Event] = {}
        self._closed = False
        self.store.recover_interrupted()

    def submit(self, request: CampaignRequest, idempotency_key: str) -> tuple[CampaignTask, bool]:
        with self._lock:
            if self._closed:
                raise RuntimeError("L'orchestrateur de campagnes est arrêté.")
            task, created = self.store.create(request, idempotency_key)
            if not created:
                return task, False
            cancel_event = threading.Event()
            self._cancel_events[task.task_id] = cancel_event
            try:
                self._worker.submit(self._run, task.task_id, cancel_event)
            except RuntimeError:
                self._cancel_events.pop(task.task_id, None)
                self.store.fail(task.task_id, error_code="worker_unavailable")
                raise
            return task, True

    def get(self, task_id: str) -> CampaignTask:
        return self.store.get(task_id)

    def check_readiness(self, check: Callable[[], ReadinessSnapshot]) -> ReadinessSnapshot:
        """Mesure la disponibilité hors campagne pour ne pas perturber un benchmark."""
        with self._lock:
            if self._closed:
                raise RuntimeError("L'orchestrateur de campagnes est arrêté.")
            active = self.store.active()
            if active is not None:
                raise EngineBusy(active)
            return check()

    def events(
        self, task_id: str, *, after_sequence: int = 0, limit: int = MAX_EVENTS_PER_TASK
    ) -> list[CampaignTaskEvent]:
        return self.store.events(task_id, after_sequence=after_sequence, limit=limit)

    def event_page(
        self, task_id: str, *, after_sequence: int = 0, limit: int = MAX_EVENTS_PER_TASK
    ) -> CampaignTaskEventPage:
        return self.store.event_page(task_id, after_sequence=after_sequence, limit=limit)

    def cancel(self, task_id: str) -> tuple[CampaignTask, bool]:
        task, accepted = self.store.request_cancel(task_id)
        if accepted:
            with self._lock:
                signal = self._cancel_events.get(task_id)
                if signal is not None:
                    signal.set()
        return task, accepted

    def close(self, *, wait: bool = True) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            active = self.store.active()
            if active is not None:
                task, accepted = self.store.request_cancel(active.task_id)
                if accepted:
                    signal = self._cancel_events.get(task.task_id)
                    if signal is not None:
                        signal.set()
        self._worker.shutdown(wait=wait, cancel_futures=False)

    def _run(self, task_id: str, cancel_event: threading.Event) -> None:
        try:
            if not self.store.mark_running(task_id):
                return
            task = self.store.get(task_id)

            def report_progress(
                benchmark_id: str, result: BenchmarkResult | BenchmarkFailure | None
            ) -> None:
                outcome: Literal["started", "succeeded", "failed"] = (
                    "started"
                    if result is None
                    else "failed"
                    if isinstance(result, BenchmarkFailure)
                    else "succeeded"
                )
                self.store.record_progress(task_id, benchmark_id, outcome=outcome, result=result)

            report: BenchmarkReport = self.executor.execute(
                task.request,
                progress=report_progress,
                should_cancel=cancel_event.is_set,
            )
            report_path = self.reports.save(report)
            digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
            self.store.finish(
                task_id,
                report_id=f"sha256:{digest}",
                execution_status=report.execution_status,
                has_failures=bool(report.failures),
            )
        except Exception:  # noqa: BLE001
            self.store.fail(task_id)
        finally:
            with self._lock:
                self._cancel_events.pop(task_id, None)
