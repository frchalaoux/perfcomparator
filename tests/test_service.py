from test_repository import sample_report

from perfcomparator import BENCHMARK_PROTOCOL_VERSION
from perfcomparator import benchmarks as benchmark_module
from perfcomparator.benchmarks import BenchmarkDefinition
from perfcomparator.executor import _environment_warnings
from perfcomparator.models import (
    BenchmarkResult,
    CampaignRequest,
    EnvironmentSnapshot,
    ReadinessSnapshot,
)
from perfcomparator.repository import JsonReportRepository
from perfcomparator.service import BenchmarkService


def test_service_aggregates_repetitions_with_the_median(tmp_path, monkeypatch) -> None:
    values = iter([10.0, 30.0, 20.0])
    gpu_indices = []

    def fake_runner(context):
        gpu_indices.append(context.gpu_index)
        return BenchmarkResult(
            benchmark_id="test.fake",
            group="test",
            name="Test",
            description="Test",
            value=next(values),
            unit="unités/s",
            elapsed_seconds=0.1,
        )

    definition = BenchmarkDefinition("test.fake", "test", "Test", "Test", fake_runner)
    monkeypatch.setitem(benchmark_module.CATALOG, "test.fake", definition)
    monkeypatch.setattr(
        "perfcomparator.executor.system_snapshot", lambda _path: sample_report().system
    )

    repository = JsonReportRepository(tmp_path / "results")
    report, path = BenchmarkService(repository).run(
        names=["test.fake"],
        profile_name="quick",
        work_dir=tmp_path,
        gpu_index=2,
        repetitions=3,
        readiness=ReadinessSnapshot(
            sample_seconds=1,
            cpu_percent=2,
            memory_available_percent=80,
            memory_available_bytes=1_000_000,
            swap_percent=0,
        ),
    )

    measured = report.results[0]
    assert measured.value == 20
    assert measured.minimum == 10
    assert measured.maximum == 30
    assert measured.relative_spread_percent == 100
    assert measured.sample_values == [10, 30, 20]
    assert report.repetitions == 3
    assert report.protocol_version == BENCHMARK_PROTOCOL_VERSION
    assert repository.load_path(path).protocol_version == BENCHMARK_PROTOCOL_VERSION
    assert report.readiness is not None
    assert report.readiness.suitable
    assert gpu_indices == [2, 2, 2]


def test_service_passes_portable_request_to_executor_and_archives_its_report(tmp_path) -> None:
    expected = sample_report(label="Campagne web")
    calls = []

    class FakeExecutor:
        def execute(self, request, *, progress=None):
            calls.append((request, progress))
            return expected

    repository = JsonReportRepository(tmp_path / "results")
    callback = lambda *_: None
    report, path = BenchmarkService(repository, executor=FakeExecutor()).run(
        names=["cpu.integer"],
        profile_name="quick",
        label="Campagne web",
        work_dir=tmp_path / "machine-specific-work-dir",
        repetitions=2,
        progress=callback,
    )

    request, received_progress = calls[0]
    assert request == CampaignRequest(
        profile="quick",
        benchmark_ids=["cpu.integer"],
        repetitions=2,
        label="Campagne web",
    )
    assert set(request.model_dump()) == {"profile", "benchmark_ids", "repetitions", "label"}
    assert received_progress is callback
    assert report is expected
    assert repository.load_path(path) == expected


def test_campaign_request_rejects_machine_specific_fields() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CampaignRequest(
            profile="quick",
            benchmark_ids=["cpu.integer"],
            repetitions=1,
            work_dir="/machine/path",
        )


def test_environment_warnings_detect_battery_thermal_limit_and_temperature() -> None:
    warnings = _environment_warnings(
        EnvironmentSnapshot(
            power_source="Battery Power",
            thermal_limit_percent=100,
            temperature_celsius=60,
        ),
        EnvironmentSnapshot(
            power_source="Battery Power",
            thermal_limit_percent=80,
            temperature_celsius=86,
        ),
    )

    assert any("batterie" in warning for warning in warnings)
    assert any("80 %" in warning for warning in warnings)
    assert any("26.0 °C" in warning for warning in warnings)
    assert any("86.0 °C" in warning for warning in warnings)
