"""Service métier : résolution de campagne et archivage du résultat."""

from __future__ import annotations

from pathlib import Path

from .benchmarks import PROFILES, resolve_benchmarks
from .executor import (
    BenchmarkExecutor,
    LocalBenchmarkExecutor,
    ProgressCallback,
)
from .models import (
    BenchmarkReport,
    CampaignRequest,
    ReadinessSnapshot,
)
from .repository import JsonReportRepository


class BenchmarkService:
    """Délègue la mesure à un exécuteur puis archive le rapport produit."""

    def __init__(
        self,
        repository: JsonReportRepository,
        executor: BenchmarkExecutor | None = None,
    ) -> None:
        self.repository = repository
        self.executor = executor

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
        """Exécute une sélection et conserve les éventuels échecs isolés."""
        if profile_name not in PROFILES:
            raise ValueError(f"Profil inconnu : {profile_name}")
        if not 1 <= repetitions <= 9:
            raise ValueError("Le nombre de répétitions doit être compris entre 1 et 9.")
        selected = resolve_benchmarks(names, groups)
        request = CampaignRequest(
            profile=profile_name,
            benchmark_ids=selected,
            repetitions=repetitions,
            label=label,
        )
        executor = self.executor
        if executor is None:
            executor = LocalBenchmarkExecutor(
                work_dir=work_dir,
                workers=workers,
                gpu_index=gpu_index,
                readiness=readiness,
            )
        report = executor.execute(request, progress=progress)
        return report, self.repository.save(report)
