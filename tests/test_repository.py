from datetime import UTC, datetime

from perfcomparator.models import BenchmarkReport, BenchmarkResult, SystemSnapshot
from perfcomparator.repository import JsonReportRepository


def sample_report(*, value: float = 10.0, label: str = "Mac test") -> BenchmarkReport:
    return BenchmarkReport(
        suite_version="0.1.0",
        recorded_at=datetime(2026, 9, 24, 10, 30, tzinfo=UTC),
        label=label,
        profile="quick",
        requested_benchmarks=["cpu.integer"],
        system=SystemSnapshot(
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
            python_executable="/python",
            disk_total_bytes=1_000_000,
            disk_free_bytes=500_000,
        ),
        results=[
            BenchmarkResult(
                benchmark_id="cpu.integer",
                group="cpu",
                name="Entiers mono-cœur",
                description="Test",
                value=value,
                unit="Mop/s",
                elapsed_seconds=1,
            )
        ],
    )


def test_repository_round_trip(tmp_path) -> None:
    repository = JsonReportRepository(tmp_path)

    path = repository.save(sample_report())

    assert path.exists()
    assert repository.reports() == [sample_report()]
    assert repository.load_path(path) == sample_report()


def test_repository_ignores_an_invalid_archive(tmp_path) -> None:
    (tmp_path / "benchmark_invalid.json").write_text("{", encoding="utf-8")

    assert JsonReportRepository(tmp_path).reports() == []
