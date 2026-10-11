"""Endpoints de lecture seule utilisés par PCWEB."""

from __future__ import annotations

import hashlib
import re
import secrets
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from perfcomparator.apis.security import require_api_token
from perfcomparator.benchmarks import (
    BENCHMARK_DOCUMENTATION,
    CATALOG,
    DEFINITIONS,
    GROUPS,
    PROFILES,
    REFERENCE_LIBRARY,
)
from perfcomparator.comparison import analyze_reports, parse_scenario_weights
from perfcomparator.core.machine_metadata import MachineMetadataOverride
from perfcomparator.gpu_benchmarks import gpu_adapters
from perfcomparator.html_report import render_html
from perfcomparator.models import BenchmarkReport
from perfcomparator.system_info import system_snapshot

from .schemas import (
    APIErrorEnvelope,
    BenchmarkCatalogResponse,
    BenchmarkDetail,
    BenchmarkGroup,
    BenchmarkProfileResponse,
    BenchmarkSummary,
    ComparisonMachineResponse,
    ComparisonMetricResponse,
    GPUAdapterResponse,
    ReportComparisonRequest,
    ReportComparisonResponse,
    ReportDetailResponse,
    ReportFailureResponse,
    ReportMachineMetadataUpdate,
    ReportMachineMetadataUpdateResponse,
    ReportPage,
    ReportResultResponse,
    ReportSummary,
    ReportSystemResponse,
    SystemEnvelope,
    SystemResponse,
)

router = APIRouter(
    dependencies=[Depends(require_api_token)],
    responses={
        401: {"model": APIErrorEnvelope},
        404: {"model": APIErrorEnvelope},
        422: {"model": APIErrorEnvelope},
        500: {"model": APIErrorEnvelope},
    },
)

_WINDOWS_SYSTEM_CACHE_SECONDS = 300
_windows_system_cache_lock = threading.Lock()
_windows_system_cache_expires_at = 0.0
_windows_system_cache_value: SystemEnvelope | None = None


def _report_entries(request: Request) -> tuple[list[tuple[str, BenchmarkReport]], int]:
    repository = request.app.state.reports
    root = repository.root
    if not root.exists():
        return [], 0
    entries: list[tuple[str, BenchmarkReport]] = []
    invalid_count = 0
    for path in sorted(root.glob("benchmark_*.json"), reverse=True):
        try:
            contents = path.read_bytes()
            report = BenchmarkReport.model_validate_json(contents)
        except OSError, ValueError:
            invalid_count += 1
            continue
        report_id = f"sha256:{hashlib.sha256(contents).hexdigest()}"
        entries.append((report_id, report))
    return entries, invalid_count


def _summary(report_id: str, report: BenchmarkReport) -> ReportSummary:
    return ReportSummary(
        report_id=report_id,
        recorded_at=report.recorded_at,
        execution_status=report.execution_status,
        label=report.label,
        profile=report.profile,
        repetitions=report.repetitions,
        machine=report.system.product_name or report.system.model,
        suite_version=report.suite_version,
        protocol_version=report.protocol_version,
        result_count=len(report.results),
        failure_count=len(report.failures),
    )


@router.get("/system", response_model=SystemEnvelope)
def get_system(request: Request) -> SystemEnvelope:
    global _windows_system_cache_expires_at, _windows_system_cache_value

    def build_response() -> SystemEnvelope:
        snapshot = system_snapshot(
            Path.home(),
            machine_metadata=request.app.state.machine_metadata.load(),
        )
        safe_system = SystemResponse.model_validate(
            snapshot.model_dump(exclude={"python_executable"})
        )
        adapters: list[GPUAdapterResponse] = []
        warnings: list[str] = []
        try:
            adapters = [GPUAdapterResponse.model_validate(asdict(item)) for item in gpu_adapters()]
        except Exception:  # noqa: BLE001 - l'inventaire système reste disponible sans WebGPU
            warnings.append("L’inventaire des adaptateurs WebGPU est indisponible.")
        else:
            if not adapters:
                warnings.append("Aucun adaptateur WebGPU compatible n’a été détecté.")
        return SystemEnvelope(system=safe_system, gpu_adapters=adapters, warnings=warnings)

    if sys.platform != "win32":
        return build_response()
    with _windows_system_cache_lock:
        now = time.monotonic()
        if _windows_system_cache_value is not None and now < _windows_system_cache_expires_at:
            return _windows_system_cache_value
        response = build_response()
        _windows_system_cache_value = response
        _windows_system_cache_expires_at = now + _WINDOWS_SYSTEM_CACHE_SECONDS
        return response


@router.patch("/system/machine", response_model=SystemEnvelope)
def update_machine_metadata(
    metadata: MachineMetadataOverride,
    request: Request,
) -> SystemEnvelope:
    global _windows_system_cache_expires_at, _windows_system_cache_value

    request.app.state.machine_metadata.save(metadata)
    with _windows_system_cache_lock:
        _windows_system_cache_value = None
        _windows_system_cache_expires_at = 0.0
    return get_system(request)


@router.get("/benchmarks", response_model=BenchmarkCatalogResponse)
def get_benchmarks() -> BenchmarkCatalogResponse:
    benchmarks = [
        BenchmarkSummary(
            benchmark_id=item.benchmark_id,
            group=item.group,
            name=item.name,
            description=item.description,
        )
        for item in DEFINITIONS
    ]
    groups = [
        BenchmarkGroup(group_id=group, benchmark_ids=list(benchmark_ids))
        for group, benchmark_ids in GROUPS.items()
    ]
    profiles = [
        BenchmarkProfileResponse(
            profile_id=profile.name,
            duration_seconds=profile.duration_seconds,
            memory_size_bytes=profile.memory_size_bytes,
            disk_size_bytes=profile.disk_size_bytes,
            random_operations=profile.random_operations,
            sqlite_rows=profile.sqlite_rows,
        )
        for profile in PROFILES.values()
    ]
    return BenchmarkCatalogResponse(benchmarks=benchmarks, groups=groups, profiles=profiles)


@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkDetail)
def get_benchmark(benchmark_id: str) -> BenchmarkDetail:
    definition = CATALOG.get(benchmark_id)
    documentation = BENCHMARK_DOCUMENTATION.get(benchmark_id)
    if definition is None or documentation is None:
        raise HTTPException(status_code=404, detail="benchmark_not_found")
    return BenchmarkDetail(
        benchmark_id=definition.benchmark_id,
        group=definition.group,
        name=definition.name,
        description=definition.description,
        methodology=documentation.methodology,
        limitations=documentation.limitations,
        unit=documentation.unit,
        references=[REFERENCE_LIBRARY[item] for item in documentation.reference_ids],
    )


@router.get("/reports", response_model=ReportPage)
def get_reports(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    q: str = Query(default="", max_length=120),
) -> ReportPage:
    entries, invalid_count = _report_entries(request)
    query = q.strip().casefold()
    if query:
        entries = [
            (report_id, report)
            for report_id, report in entries
            if any(
                query in value.casefold()
                for value in (
                    report.label or "",
                    report.system.product_name or "",
                    report.system.model or "",
                    report.system.manufacturer or "",
                    report.system.processor or "",
                    report.system.machine or "",
                )
            )
        ]
    return ReportPage(
        reports=[
            _summary(report_id, report) for report_id, report in entries[offset : offset + limit]
        ],
        offset=offset,
        limit=limit,
        total=len(entries),
        warnings=(["Des archives JSON illisibles ont été ignorées."] if invalid_count else []),
    )


@router.get("/reports/{report_id}", response_model=ReportDetailResponse)
def get_report(report_id: str, request: Request) -> ReportDetailResponse:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", report_id) is None:
        raise HTTPException(status_code=404, detail="report_not_found")
    entries, _ = _report_entries(request)
    for candidate_id, report in entries:
        if secrets.compare_digest(candidate_id, report_id):
            summary = _summary(candidate_id, report)
            return ReportDetailResponse(
                **summary.model_dump(),
                requested_benchmarks=[
                    benchmark_id
                    for benchmark_id in report.requested_benchmarks
                    if benchmark_id in CATALOG
                ],
                system=ReportSystemResponse(
                    system=report.system.system,
                    release=report.system.release,
                    machine=report.system.machine,
                    model=report.system.model,
                    model_year=report.system.model_year,
                    product_sku=report.system.product_sku,
                    manufacturer=report.system.manufacturer,
                    product_name=report.system.product_name,
                    processor=report.system.processor,
                    physical_cpu_count=report.system.physical_cpu_count,
                    logical_cpu_count=report.system.logical_cpu_count,
                    memory_bytes=report.system.memory_bytes,
                    gpu_devices=report.system.gpu_devices,
                    python_version=report.system.python_version,
                    python_implementation=report.system.python_implementation,
                ),
                environment_warnings=report.environment_warnings,
                results=[
                    ReportResultResponse(
                        benchmark_id=result.benchmark_id,
                        group=CATALOG[result.benchmark_id].group,
                        name=CATALOG[result.benchmark_id].name,
                        value=result.value,
                        unit=BENCHMARK_DOCUMENTATION[result.benchmark_id].unit,
                        higher_is_better=result.higher_is_better,
                        elapsed_seconds=result.elapsed_seconds,
                        repetitions=result.repetitions,
                        sample_values=result.sample_values,
                        minimum=result.minimum,
                        maximum=result.maximum,
                        relative_spread_percent=result.relative_spread_percent,
                        methodology=BENCHMARK_DOCUMENTATION[result.benchmark_id].methodology,
                        limitations=BENCHMARK_DOCUMENTATION[result.benchmark_id].limitations,
                        references=[
                            REFERENCE_LIBRARY[item]
                            for item in BENCHMARK_DOCUMENTATION[result.benchmark_id].reference_ids
                        ],
                    )
                    for result in report.results
                    if result.benchmark_id in CATALOG
                    and result.benchmark_id in BENCHMARK_DOCUMENTATION
                ],
                failures=[
                    ReportFailureResponse(
                        benchmark_id=failure.benchmark_id,
                        message="Ce benchmark a échoué dans cet environnement.",
                    )
                    for failure in report.failures
                    if failure.benchmark_id in CATALOG
                ],
            )
    raise HTTPException(status_code=404, detail="report_not_found")


@router.patch(
    "/reports/{report_id}/machine",
    response_model=ReportMachineMetadataUpdateResponse,
)
def update_report_machine(
    report_id: str,
    body: ReportMachineMetadataUpdate,
    request: Request,
) -> ReportMachineMetadataUpdateResponse:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", report_id) is None:
        raise HTTPException(status_code=404, detail="report_not_found")

    root = request.app.state.reports.root
    if not root.exists():
        raise HTTPException(status_code=404, detail="report_not_found")
    for path in sorted(root.glob("benchmark_*.json"), reverse=True):
        try:
            contents = path.read_bytes()
            candidate_id = f"sha256:{hashlib.sha256(contents).hexdigest()}"
            if not secrets.compare_digest(candidate_id, report_id):
                continue
            report = BenchmarkReport.model_validate_json(contents)
        except (OSError, ValueError):
            continue

        model = body.model.strip()
        if not model:
            raise HTTPException(status_code=422, detail="model_required")
        system = report.system.model_copy(
            update={
                "model": model,
                "model_year": body.model_year,
                "product_sku": body.product_sku,
            }
        )
        updated = report.model_copy(update={"system": system})
        serialized = updated.model_dump_json(indent=2).encode("utf-8")
        temporary = path.with_name(f"{path.name}.edit.tmp")
        try:
            temporary.write_bytes(serialized)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return ReportMachineMetadataUpdateResponse(
            report_id=f"sha256:{hashlib.sha256(serialized).hexdigest()}",
            model=model,
            model_year=body.model_year,
            product_sku=body.product_sku,
        )
    raise HTTPException(status_code=404, detail="report_not_found")


@router.post("/reports/compare", response_model=ReportComparisonResponse)
def compare_reports(body: ReportComparisonRequest, request: Request) -> ReportComparisonResponse:
    if len(set(body.report_ids)) != len(body.report_ids):
        raise HTTPException(status_code=422, detail="comparison_rejected")
    if body.reference_report_id not in body.report_ids:
        raise HTTPException(status_code=422, detail="comparison_rejected")
    if any(re.fullmatch(r"sha256:[0-9a-f]{64}", item) is None for item in body.report_ids):
        raise HTTPException(status_code=404, detail="report_not_found")

    entries, _ = _report_entries(request)
    reports_by_id = dict(entries)
    if any(report_id not in reports_by_id for report_id in body.report_ids):
        raise HTTPException(status_code=404, detail="report_not_found")

    ordered_ids = [body.reference_report_id] + [
        report_id for report_id in body.report_ids if report_id != body.reference_report_id
    ]
    reports = [reports_by_id[report_id] for report_id in ordered_ids]
    try:
        analysis = analyze_reports(reports, parse_scenario_weights(None))
    except ValueError as error:
        raise HTTPException(status_code=422, detail="comparison_rejected") from error

    machines = []
    for report_id, machine in zip(ordered_ids, analysis.machines, strict=True):
        report = machine.report
        machines.append(
            ComparisonMachineResponse(
                report_id=report_id,
                label=machine.label,
                recorded_at=report.recorded_at,
                profile=report.profile,
                system=ReportSystemResponse(
                    system=report.system.system,
                    release=report.system.release,
                    machine=report.system.machine,
                    model=report.system.model,
                    model_year=report.system.model_year,
                    product_sku=report.system.product_sku,
                    manufacturer=report.system.manufacturer,
                    product_name=report.system.product_name,
                    processor=report.system.processor,
                    physical_cpu_count=report.system.physical_cpu_count,
                    logical_cpu_count=report.system.logical_cpu_count,
                    memory_bytes=report.system.memory_bytes,
                    gpu_devices=report.system.gpu_devices,
                    python_version=report.system.python_version,
                    python_implementation=report.system.python_implementation,
                ),
                overall_index=machine.overall_index,
                categories=machine.categories,
                scenarios=machine.scenarios,
                narrative=machine.narrative,
                metrics={
                    benchmark_id: ComparisonMetricResponse(
                        benchmark_id=metric.benchmark_id,
                        name=metric.name,
                        group=metric.group,
                        value=metric.value,
                        unit=metric.unit,
                        index=metric.index,
                        difference_percent=metric.difference_percent,
                        conclusion=metric.conclusion,
                        uncertainty=metric.uncertainty,
                        spread_percent=metric.spread_percent,
                    )
                    for benchmark_id, metric in machine.metrics.items()
                },
            )
        )
    return ReportComparisonResponse(
        baseline_report_id=body.reference_report_id,
        baseline_label=analysis.baseline_label,
        common_benchmarks=list(analysis.common_benchmarks),
        scenario_weights=analysis.scenario_weights,
        warnings=list(analysis.warnings),
        machines=machines,
    )


@router.post("/comparisons/export", response_class=HTMLResponse)
def export_comparison(body: ReportComparisonRequest, request: Request) -> HTMLResponse:
    if len(set(body.report_ids)) != len(body.report_ids):
        raise HTTPException(status_code=422, detail="comparison_rejected")
    if body.reference_report_id not in body.report_ids:
        raise HTTPException(status_code=422, detail="comparison_rejected")
    if any(re.fullmatch(r"sha256:[0-9a-f]{64}", item) is None for item in body.report_ids):
        raise HTTPException(status_code=404, detail="report_not_found")

    entries, _ = _report_entries(request)
    reports_by_id = dict(entries)
    if any(report_id not in reports_by_id for report_id in body.report_ids):
        raise HTTPException(status_code=404, detail="report_not_found")
    ordered_ids = [body.reference_report_id] + [
        report_id for report_id in body.report_ids if report_id != body.reference_report_id
    ]
    try:
        analysis = analyze_reports(
            [reports_by_id[report_id] for report_id in ordered_ids],
            parse_scenario_weights(None),
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="comparison_rejected") from error
    return HTMLResponse(content=render_html(analysis))
