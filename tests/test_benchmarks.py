import sqlite3
from pathlib import Path

import pytest

import perfcomparator.benchmarks as benchmark_module
from perfcomparator.benchmarks import (
    CATALOG,
    DEFINITIONS,
    BenchmarkContext,
    BenchmarkProfile,
    resolve_benchmarks,
)


@pytest.fixture
def tiny_context(tmp_path: Path) -> BenchmarkContext:
    return BenchmarkContext(
        profile=BenchmarkProfile(
            name="test",
            duration_seconds=0.01,
            memory_size_bytes=64 * 1_024,
            disk_size_bytes=1_048_576,
            random_operations=16,
            sqlite_rows=50,
        ),
        work_dir=tmp_path,
        workers=2,
    )


@pytest.mark.parametrize("definition", DEFINITIONS, ids=lambda item: item.benchmark_id)
def test_each_benchmark_returns_its_declared_result(definition, tiny_context) -> None:
    result = definition.runner(tiny_context)

    assert result.benchmark_id == definition.benchmark_id
    assert result.group == definition.group
    assert result.value > 0
    assert result.elapsed_seconds > 0
    assert result.methodology
    assert result.limitations
    assert result.references


def test_resolve_benchmarks_supports_groups_and_individual_names() -> None:
    selected = resolve_benchmarks(["memory.copy"], ["application"])

    assert selected == ["application.json", "application.sqlite", "memory.copy"]


def test_resolve_benchmarks_defaults_to_the_complete_catalog() -> None:
    assert resolve_benchmarks(None, None) == list(CATALOG)


def test_resolve_benchmarks_rejects_unknown_names() -> None:
    with pytest.raises(ValueError, match="inconnu"):
        resolve_benchmarks(["gpu.magic"], None)


def test_sqlite_connection_is_closed_before_temporary_directory_cleanup(
    monkeypatch: pytest.MonkeyPatch, tiny_context: BenchmarkContext
) -> None:
    original_connect = sqlite3.connect
    connections: list[TrackingConnection] = []

    class TrackingConnection(sqlite3.Connection):
        was_closed = False

        def close(self) -> None:
            self.was_closed = True
            super().close()

    def tracked_connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs, factory=TrackingConnection)
        connections.append(connection)
        return connection

    monkeypatch.setattr(benchmark_module.sqlite3, "connect", tracked_connect)

    try:
        result = benchmark_module.application_sqlite(tiny_context)
        assert result.value > 0
        assert len(connections) == 1
        assert connections[0].was_closed
    finally:
        for connection in connections:
            if not connection.was_closed:
                connection.close()
