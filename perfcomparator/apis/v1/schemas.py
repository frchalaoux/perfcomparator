"""Réponses publiques et sans chemins privés de l’API de lecture PCE."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GPUAdapterResponse(BaseModel):
    index: int
    device: str
    backend: str
    adapter_type: str


class SystemResponse(BaseModel):
    system: str
    release: str
    version: str
    machine: str
    model: str
    manufacturer: str | None
    product_name: str | None
    model_year: int | None
    product_sku: str | None
    processor: str
    physical_cpu_count: int | None
    logical_cpu_count: int
    memory_bytes: int | None
    gpu_devices: list[str]
    python_version: str
    python_implementation: str
    disk_total_bytes: int
    disk_free_bytes: int


class SystemEnvelope(BaseModel):
    system: SystemResponse
    gpu_adapters: list[GPUAdapterResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class APIErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class APIErrorEnvelope(BaseModel):
    error: APIErrorDetail


class BenchmarkSummary(BaseModel):
    benchmark_id: str
    group: str
    name: str
    description: str


class BenchmarkDetail(BenchmarkSummary):
    methodology: str
    limitations: str
    unit: str
    references: list[str]


class BenchmarkGroup(BaseModel):
    group_id: str
    benchmark_ids: list[str]


class BenchmarkProfileResponse(BaseModel):
    profile_id: str
    duration_seconds: float
    memory_size_bytes: int
    disk_size_bytes: int
    random_operations: int
    sqlite_rows: int


class BenchmarkCatalogResponse(BaseModel):
    benchmarks: list[BenchmarkSummary]
    groups: list[BenchmarkGroup]
    profiles: list[BenchmarkProfileResponse]


class ReportSummary(BaseModel):
    report_id: str
    recorded_at: datetime
    label: str | None
    profile: str
    repetitions: int
    machine: str
    suite_version: str
    protocol_version: str | None
    result_count: int
    failure_count: int


class ReportPage(BaseModel):
    reports: list[ReportSummary]
    offset: int
    limit: int
    total: int
    warnings: list[str] = Field(default_factory=list)


class ReportSystemResponse(BaseModel):
    system: str
    release: str
    machine: str
    model: str
    manufacturer: str | None
    product_name: str | None
    processor: str
    physical_cpu_count: int | None
    logical_cpu_count: int
    memory_bytes: int | None
    gpu_devices: list[str]


class ReportResultResponse(BaseModel):
    benchmark_id: str
    group: str
    name: str
    value: float
    unit: str
    higher_is_better: bool
    elapsed_seconds: float
    repetitions: int
    sample_values: list[float]
    minimum: float | None
    maximum: float | None
    relative_spread_percent: float | None
    methodology: str
    limitations: str
    references: list[str]


class ReportFailureResponse(BaseModel):
    benchmark_id: str
    message: str


class ReportDetailResponse(ReportSummary):
    requested_benchmarks: list[str]
    system: ReportSystemResponse
    environment_warnings: list[str]
    results: list[ReportResultResponse]
    failures: list[ReportFailureResponse]
