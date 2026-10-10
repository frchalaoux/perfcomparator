"""Frontière entre une demande de campagne et son exécution sur un hôte."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Protocol

from . import BENCHMARK_PROTOCOL_VERSION, __version__
from .benchmarks import CATALOG, PROFILES, BenchmarkContext
from .models import (
    BenchmarkFailure,
    BenchmarkReport,
    BenchmarkResult,
    CampaignRequest,
    EnvironmentSnapshot,
    ReadinessSnapshot,
)
from .system_info import environment_snapshot, machine_readiness, system_snapshot

ProgressCallback = Callable[[str, BenchmarkResult | BenchmarkFailure | None], None]


class BenchmarkExecutor(Protocol):
    """Exécute une demande portable et retourne un rapport, sans l'archiver."""

    def execute(
        self,
        request: CampaignRequest,
        *,
        progress: ProgressCallback | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> BenchmarkReport:
        """Exécute les benchmarks sélectionnés et produit le rapport associé."""


def _environment_warnings(start: EnvironmentSnapshot, end: EnvironmentSnapshot) -> list[str]:
    warnings: list[str] = []
    for snapshot in (start, end):
        if snapshot.power_source and "battery" in snapshot.power_source.lower():
            warnings.append("Campagne exécutée au moins partiellement sur batterie.")
            break
    if start.power_source and end.power_source and start.power_source != end.power_source:
        warnings.append("La source d'alimentation a changé pendant la campagne.")
    limits = [
        value
        for value in (start.thermal_limit_percent, end.thermal_limit_percent)
        if value is not None
    ]
    if limits and min(limits) < 100:
        warnings.append(f"Limitation thermique détectée : vitesse CPU limitée à {min(limits)} %.")
    if start.temperature_celsius is not None and end.temperature_celsius is not None:
        change = end.temperature_celsius - start.temperature_celsius
        if change >= 10:
            warnings.append(f"Température en hausse de {change:.1f} °C pendant la campagne.")
        if end.temperature_celsius >= 85:
            warnings.append(f"Température finale élevée : {end.temperature_celsius:.1f} °C.")
    return warnings


class LocalBenchmarkExecutor:
    """Exécute localement les runners et les relevés propres à la machine."""

    def __init__(
        self,
        *,
        work_dir: Path | str = ".",
        workers: int | None = None,
        gpu_index: int | None = None,
        readiness: ReadinessSnapshot | None = None,
    ) -> None:
        self.work_dir = Path(work_dir)
        self.workers = workers
        self.gpu_index = gpu_index
        self.readiness = readiness

    def execute(
        self,
        request: CampaignRequest,
        *,
        progress: ProgressCallback | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> BenchmarkReport:
        if request.profile not in PROFILES:
            raise ValueError(f"Profil inconnu : {request.profile}")
        unknown = [
            benchmark_id for benchmark_id in request.benchmark_ids if benchmark_id not in CATALOG
        ]
        if unknown:
            raise ValueError(f"Benchmark inconnu : {unknown[0]}")

        self.work_dir.mkdir(parents=True, exist_ok=True)
        work_dir = self.work_dir.resolve()
        context = BenchmarkContext(
            profile=PROFILES[request.profile],
            work_dir=work_dir,
            workers=self.workers or (os.cpu_count() or 1),
            gpu_index=self.gpu_index,
        )
        results: list[BenchmarkResult] = []
        failures: list[BenchmarkFailure] = []
        cancelled = False
        readiness = self.readiness or machine_readiness()
        environment_start = environment_snapshot()
        for benchmark_id in request.benchmark_ids:
            if should_cancel and should_cancel():
                cancelled = True
                break
            if progress:
                progress(benchmark_id, None)
            samples = []
            runner_failed = False
            try:
                for _ in range(request.repetitions):
                    if should_cancel and should_cancel():
                        cancelled = True
                        break
                    samples.append(CATALOG[benchmark_id].runner(context))
            # L'isolation est volontaire : un test matériel peut échouer de façon imprévisible.
            except Exception as error:  # noqa: BLE001
                runner_failed = True
                failure = BenchmarkFailure(benchmark_id=benchmark_id, message=str(error))
                failures.append(failure)
                if progress:
                    progress(benchmark_id, failure)
            if samples and not runner_failed:
                values = [sample.value for sample in samples]
                center = median(values)
                minimum = min(values)
                maximum = max(values)
                result = samples[0].model_copy(
                    update={
                        "value": center,
                        "elapsed_seconds": median([sample.elapsed_seconds for sample in samples]),
                        "repetitions": len(samples),
                        "sample_values": values,
                        "minimum": minimum,
                        "maximum": maximum,
                        "relative_spread_percent": (maximum - minimum) / center * 100,
                    }
                )
                results.append(result)
                if progress:
                    progress(benchmark_id, result)
            if cancelled:
                break
        environment_end = environment_snapshot()
        cancelled = cancelled or bool(should_cancel and should_cancel())
        return BenchmarkReport(
            execution_status="cancelled" if cancelled else "completed",
            suite_version=__version__,
            protocol_version=BENCHMARK_PROTOCOL_VERSION,
            recorded_at=datetime.now(UTC),
            label=request.label,
            profile=request.profile,
            repetitions=request.repetitions,
            requested_benchmarks=request.benchmark_ids,
            system=system_snapshot(work_dir),
            environment_start=environment_start,
            environment_end=environment_end,
            environment_warnings=_environment_warnings(environment_start, environment_end),
            readiness=readiness,
            results=results,
            failures=failures,
        )
