from test_repository import sample_report

from perfcomparator import BENCHMARK_PROTOCOL_VERSION
from perfcomparator import benchmarks as benchmark_module
from perfcomparator.benchmarks import BenchmarkDefinition
from perfcomparator.models import BenchmarkResult, EnvironmentSnapshot, ReadinessSnapshot
from perfcomparator.repository import JsonReportRepository
from perfcomparator.service import BenchmarkService, _environment_warnings


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
        "perfcomparator.service.system_snapshot", lambda _path: sample_report().system
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
