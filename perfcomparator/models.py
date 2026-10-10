"""Contrats validés utilisés par la suite et les archives JSON."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SystemSnapshot(BaseModel):
    """Machine et environnement logiciel associés à chaque mesure."""

    system: str
    release: str
    version: str
    machine: str
    model: str
    manufacturer: str | None = None
    product_name: str | None = None
    model_year: int | None = Field(default=None, ge=1984, le=2100)
    product_sku: str | None = None
    processor: str
    physical_cpu_count: int | None = Field(default=None, gt=0)
    logical_cpu_count: int = Field(gt=0)
    memory_bytes: int | None = Field(default=None, gt=0)
    gpu_devices: list[str] = Field(default_factory=list)
    python_version: str
    python_implementation: str
    python_executable: str
    disk_total_bytes: int = Field(gt=0)
    disk_free_bytes: int = Field(ge=0)


class EnvironmentSnapshot(BaseModel):
    """Conditions susceptibles d'influencer une campagne de mesures."""

    power_source: str | None = None
    thermal_limit_percent: int | None = Field(default=None, ge=0, le=100)
    temperature_celsius: float | None = Field(default=None, ge=-20, le=150)


class ProcessLoad(BaseModel):
    """Processus actif observé pendant le contrôle préalable."""

    pid: int = Field(gt=0)
    name: str
    cpu_percent: float = Field(ge=0)
    memory_percent: float = Field(ge=0)


class ReadinessSnapshot(BaseModel):
    """État de charge observé juste avant la campagne."""

    sample_seconds: float = Field(gt=0)
    cpu_percent: float = Field(ge=0, le=100)
    memory_available_percent: float = Field(ge=0, le=100)
    memory_available_bytes: int = Field(ge=0)
    swap_percent: float = Field(ge=0, le=100)
    active_processes: list[ProcessLoad] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suitable: bool = True


class CampaignRequest(BaseModel):
    """Choix de mesure portables, indépendants de l'hôte qui les exécute."""

    model_config = ConfigDict(extra="forbid")

    profile: str = Field(min_length=1, max_length=32)
    benchmark_ids: list[str] = Field(min_length=1, max_length=100)
    repetitions: int = Field(ge=1, le=9)
    label: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def choices_must_exist_in_catalog(self) -> CampaignRequest:
        from .benchmarks import CATALOG, PROFILES

        if self.profile not in PROFILES:
            raise ValueError(f"Profil inconnu : {self.profile}")
        unknown = [
            benchmark_id for benchmark_id in self.benchmark_ids if benchmark_id not in CATALOG
        ]
        if unknown:
            raise ValueError(f"Benchmark inconnu : {unknown[0]}")
        return self

    @field_validator("benchmark_ids")
    @classmethod
    def benchmark_ids_must_be_unique(cls, value: list[str]) -> list[str]:
        if any(not benchmark_id or len(benchmark_id) > 100 for benchmark_id in value):
            raise ValueError("Chaque ID de benchmark doit contenir de 1 à 100 caractères.")
        if len(value) != len(set(value)):
            raise ValueError("La demande contient des IDs de benchmark en double.")
        return value


class BenchmarkResult(BaseModel):
    """Mesure principale normalisée d'un benchmark."""

    benchmark_id: str
    group: str
    name: str
    description: str
    value: float = Field(gt=0)
    unit: str
    higher_is_better: bool = True
    elapsed_seconds: float = Field(gt=0)
    parameters: dict[str, int | float | str] = Field(default_factory=dict)
    methodology: str = ""
    limitations: str = ""
    references: list[str] = Field(default_factory=list)
    repetitions: int = Field(default=1, gt=0)
    sample_values: list[float] = Field(default_factory=list)
    minimum: float | None = Field(default=None, gt=0)
    maximum: float | None = Field(default=None, gt=0)
    relative_spread_percent: float | None = Field(default=None, ge=0)


class BenchmarkFailure(BaseModel):
    """Échec isolé qui n'empêche pas les autres mesures de s'exécuter."""

    benchmark_id: str
    message: str


class BenchmarkReport(BaseModel):
    """Rapport complet, portable et comparable d'une exécution."""

    schema_version: int = 7
    execution_status: Literal["completed", "cancelled"] = "completed"
    suite_version: str
    protocol_version: str | None = None
    recorded_at: datetime
    label: str | None = None
    profile: str
    repetitions: int = Field(default=1, gt=0)
    requested_benchmarks: list[str]
    system: SystemSnapshot
    environment_start: EnvironmentSnapshot | None = None
    environment_end: EnvironmentSnapshot | None = None
    environment_warnings: list[str] = Field(default_factory=list)
    readiness: ReadinessSnapshot | None = None
    results: list[BenchmarkResult]
    failures: list[BenchmarkFailure] = Field(default_factory=list)


class PublicSystemSnapshot(BaseModel):
    """Inventaire matériel minimal autorisé dans un rapport public."""

    model_config = ConfigDict(extra="forbid")

    operating_system: str
    architecture: str
    manufacturer: str | None = None
    commercial_name: str | None = None
    model_identifier: str | None = None
    product_sku: str | None = None
    processor: str
    physical_cpu_count: int | None = Field(default=None, gt=0)
    logical_cpu_count: int = Field(gt=0)
    memory_bytes: int | None = Field(default=None, gt=0)
    gpu_devices: list[str] = Field(default_factory=list)
    python_version: str
    python_implementation: str


class PublicBenchmarkResult(BaseModel):
    """Données numériques strictement nécessaires aux comparaisons."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str
    group: str
    name: str
    value: float = Field(gt=0)
    unit: str
    higher_is_better: bool = True
    parameters: dict[str, int | float | str] = Field(default_factory=dict)
    repetitions: int = Field(gt=0)
    sample_values: list[float]
    minimum: float | None = Field(default=None, gt=0)
    maximum: float | None = Field(default=None, gt=0)
    relative_spread_percent: float | None = Field(default=None, ge=0)


class PublicBenchmarkReport(BaseModel):
    """Format public fermé, déterministe et indépendant du rapport privé."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["perfcomparator-public-report"] = "perfcomparator-public-report"
    format_version: Literal[1, 2, 3] = 3
    report_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    license: Literal["CC0-1.0"] = "CC0-1.0"
    verification: Literal["community-unverified"] = "community-unverified"
    source_schema_version: Literal[3, 4, 5, 6, 7] = 7
    suite_version: str
    protocol_version: Literal["0.3.0"] = "0.3.0"
    profile: str
    repetitions: int = Field(gt=0)
    requested_benchmarks: list[str]
    system: PublicSystemSnapshot
    readiness_suitable: bool | None = None
    results: list[PublicBenchmarkResult]
    failed_benchmarks: list[str] = Field(default_factory=list)
