"""Orchestration, isolation des échecs et archivage de la suite."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from . import BENCHMARK_PROTOCOL_VERSION, __version__
from .benchmarks import CATALOG, PROFILES, BenchmarkContext, resolve_benchmarks
from .models import (
    BenchmarkFailure,
    BenchmarkReport,
    BenchmarkResult,
    EnvironmentSnapshot,
    ReadinessSnapshot,
)
from .repository import JsonReportRepository
from .system_info import environment_snapshot, machine_readiness, system_snapshot

ProgressCallback = Callable[[str, BenchmarkResult | BenchmarkFailure | None], None]


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


class BenchmarkService:
    """Exécute une sélection reproductible sans dépendre de la CLI."""

    def __init__(self, repository: JsonReportRepository) -> None:
        self.repository = repository

    def run(
        self,
        names: list[str] | None = None,
        groups: list[str] | None = None,
        *,
        profile_name: str = "standard",
        label: str | None = None,
        work_dir: Path | str = ".",
        workers: int | None = None,
        gpu_index: int | None = None,
        repetitions: int = 3,
        readiness: ReadinessSnapshot | None = None,
        progress: ProgressCallback | None = None,
    ) -> tuple[BenchmarkReport, Path]:
        """Exécute chaque test demandé et conserve les éventuels échecs isolés."""
        if profile_name not in PROFILES:
            raise ValueError(f"Profil inconnu : {profile_name}")
        if not 1 <= repetitions <= 9:
            raise ValueError("Le nombre de répétitions doit être compris entre 1 et 9.")
        selected = resolve_benchmarks(names, groups)
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        context = BenchmarkContext(
            profile=PROFILES[profile_name],
            work_dir=Path(work_dir).resolve(),
            workers=workers or (os.cpu_count() or 1),
            gpu_index=gpu_index,
        )
        results: list[BenchmarkResult] = []
        failures: list[BenchmarkFailure] = []
        readiness = readiness or machine_readiness()
        environment_start = environment_snapshot()
        for benchmark_id in selected:
            if progress:
                progress(benchmark_id, None)
            try:
                samples = [CATALOG[benchmark_id].runner(context) for _ in range(repetitions)]
            # L'isolation est volontaire : un test matériel peut échouer de façon imprévisible.
            except Exception as error:  # noqa: BLE001
                failure = BenchmarkFailure(benchmark_id=benchmark_id, message=str(error))
                failures.append(failure)
                if progress:
                    progress(benchmark_id, failure)
            else:
                values = [sample.value for sample in samples]
                center = median(values)
                minimum = min(values)
                maximum = max(values)
                result = samples[0].model_copy(
                    update={
                        "value": center,
                        "elapsed_seconds": median([sample.elapsed_seconds for sample in samples]),
                        "repetitions": repetitions,
                        "sample_values": values,
                        "minimum": minimum,
                        "maximum": maximum,
                        "relative_spread_percent": (maximum - minimum) / center * 100,
                    }
                )
                results.append(result)
                if progress:
                    progress(benchmark_id, result)
        environment_end = environment_snapshot()
        report = BenchmarkReport(
            suite_version=__version__,
            protocol_version=BENCHMARK_PROTOCOL_VERSION,
            recorded_at=datetime.now(UTC),
            label=label,
            profile=profile_name,
            repetitions=repetitions,
            requested_benchmarks=selected,
            system=system_snapshot(context.work_dir),
            environment_start=environment_start,
            environment_end=environment_end,
            environment_warnings=_environment_warnings(environment_start, environment_end),
            readiness=readiness,
            results=results,
            failures=failures,
        )
        return report, self.repository.save(report)
