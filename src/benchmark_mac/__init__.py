"""PerfComparator, suite locale pour macOS, Windows et Linux."""

from .models import BenchmarkReport, BenchmarkResult, SystemSnapshot

__all__ = [
    "BENCHMARK_PROTOCOL_VERSION",
    "BenchmarkReport",
    "BenchmarkResult",
    "SystemSnapshot",
]
__version__ = "0.5.0"
BENCHMARK_PROTOCOL_VERSION = "0.3.0"
