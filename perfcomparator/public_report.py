"""Construction sûre et déterministe des rapports destinés au catalogue public."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from .apple_models import apple_model_year
from .benchmarks import BENCHMARK_DOCUMENTATION, CATALOG, PROFILES, REFERENCE_LIBRARY
from .comparison import report_protocol
from .models import (
    BenchmarkFailure,
    BenchmarkReport,
    BenchmarkResult,
    PublicBenchmarkReport,
    PublicBenchmarkResult,
    PublicSystemSnapshot,
    SystemSnapshot,
)

PUBLIC_FORMAT_VERSION = 3
PUBLIC_LICENSE = "CC0-1.0"
MAX_PUBLIC_REPORT_BYTES = 2 * 1_048_576
SUPPORTED_PRIVATE_SCHEMAS = frozenset({3, 4, 5, 6})
SUPPORTED_PROTOCOL = "0.3.0"
SUITE_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:\.dev\d+)?$")
PRIVATE_PATH_PATTERNS = (
    re.compile(r"/(?:Users|home)/[^/]+(?:/|$)", re.IGNORECASE),
    re.compile(r"[A-Z]:\\Users\\[^\\]+(?:\\|$)", re.IGNORECASE),
)
PUBLIC_RESULT_UNITS = {
    "application.json": "cycles/s",
    "application.sqlite": "lignes/s",
    "cpu.compression": "Mio/s",
    "cpu.float": "Mop/s",
    "cpu.hash": "Mio/s",
    "cpu.integer": "Mop/s",
    "cpu.multicore": "Mop/s",
    "gpu.compute-fp32": "GFLOP/s",
    "gpu.image-filter": "Mpixel/s",
    "gpu.memory": "Gio/s",
    "gpu.raster": "Mpixel/s",
    "memory.copy": "Mio/s",
    "storage.random-read": "IOPS",
    "storage.random-write": "IOPS",
    "storage.read": "Mio/s",
    "storage.write": "Mio/s",
}
PUBLIC_PARAMETERS_BY_BENCHMARK = {
    "application.json": frozenset({"document_size_bytes"}),
    "application.sqlite": frozenset({"rows"}),
    "cpu.compression": frozenset({"block_size_bytes", "compression_level"}),
    "cpu.float": frozenset({"workers"}),
    "cpu.hash": frozenset({"block_size_bytes"}),
    "cpu.integer": frozenset({"workers"}),
    "cpu.multicore": frozenset({"workers"}),
    "gpu.compute-fp32": frozenset(
        {
            "element_count",
            "gpu_adapter_type",
            "gpu_backend",
            "gpu_device",
            "gpu_index",
            "operations_per_element",
            "wgpu_version",
        }
    ),
    "gpu.image-filter": frozenset(
        {
            "gpu_adapter_type",
            "gpu_backend",
            "gpu_device",
            "gpu_index",
            "height",
            "samples_per_pixel",
            "wgpu_version",
            "width",
        }
    ),
    "gpu.memory": frozenset(
        {
            "buffer_size_bytes",
            "bytes_counted_per_element",
            "gpu_adapter_type",
            "gpu_backend",
            "gpu_device",
            "gpu_index",
            "wgpu_version",
        }
    ),
    "gpu.raster": frozenset(
        {
            "color_format",
            "gpu_adapter_type",
            "gpu_backend",
            "gpu_device",
            "gpu_index",
            "height",
            "wgpu_version",
            "width",
        }
    ),
    "memory.copy": frozenset({"buffer_size_bytes"}),
    "storage.random-read": frozenset({"block_size_bytes", "operations"}),
    "storage.random-write": frozenset({"block_size_bytes", "operations"}),
    "storage.read": frozenset({"file_size_bytes"}),
    "storage.write": frozenset({"file_size_bytes"}),
}


def _clean_public_text(value: str, *, field: str, maximum: int = 200) -> str:
    """Refuse les chaînes ambiguës plutôt que de publier une valeur inattendue."""
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"Valeur publique invalide pour {field}.")
    if any(character in normalized for character in ("\x00", "\r", "\n")):
        raise ValueError(f"Valeur publique invalide pour {field}.")
    if any(pattern.search(normalized) for pattern in PRIVATE_PATH_PATTERNS):
        raise ValueError(f"Chemin privé détecté dans {field}.")
    return normalized


def _public_result(report_result) -> PublicBenchmarkResult:
    definition = CATALOG.get(report_result.benchmark_id)
    if definition is None:
        raise ValueError(f"Benchmark inconnu : {report_result.benchmark_id}")
    if report_result.group != definition.group:
        raise ValueError(f"Groupe incohérent pour {report_result.benchmark_id}.")
    if report_result.unit != PUBLIC_RESULT_UNITS[report_result.benchmark_id]:
        raise ValueError(f"Unité incohérente pour {report_result.benchmark_id}.")
    if not report_result.higher_is_better:
        raise ValueError(f"Sens de mesure incohérent pour {report_result.benchmark_id}.")
    expected_parameters = PUBLIC_PARAMETERS_BY_BENCHMARK[report_result.benchmark_id]
    if set(report_result.parameters) != expected_parameters:
        raise ValueError(f"Paramètres incohérents pour {report_result.benchmark_id}.")
    parameters: dict[str, int | float | str] = {}
    for name, value in sorted(report_result.parameters.items()):
        clean_name = _clean_public_text(name, field="parameters", maximum=80)
        if isinstance(value, int | float) and not math.isfinite(value):
            raise ValueError(f"Paramètre non fini pour {report_result.benchmark_id}.")
        parameters[clean_name] = (
            _clean_public_text(value, field=f"parameters.{clean_name}")
            if isinstance(value, str)
            else value
        )
    return PublicBenchmarkResult(
        benchmark_id=definition.benchmark_id,
        group=definition.group,
        name=definition.name,
        value=report_result.value,
        unit=_clean_public_text(report_result.unit, field="unit", maximum=40),
        higher_is_better=report_result.higher_is_better,
        parameters=parameters,
        repetitions=report_result.repetitions,
        sample_values=report_result.sample_values,
        minimum=report_result.minimum,
        maximum=report_result.maximum,
        relative_spread_percent=report_result.relative_spread_percent,
    )


def _content_id(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def suggest_public_machine_name(report: BenchmarkReport) -> str:
    """Propose un nom modifiable, avec l'année Apple connue si elle est certaine."""
    manufacturer = (report.system.manufacturer or "").strip()
    product_name = (report.system.product_name or "").strip()
    model = report.system.model.strip()
    if report.system.system == "Darwin":
        manufacturer = manufacturer or "Apple"
        if not product_name:
            family = re.sub(r"\d.*$", "", model)
            product_name = {
                "MacBook": "MacBook",
                "MacBookAir": "MacBook Air",
                "MacBookPro": "MacBook Pro",
                "Macmini": "Mac mini",
                "MacPro": "Mac Pro",
                "iMac": "iMac",
                "iMacPro": "iMac Pro",
            }.get(family, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", family))
        product_name = product_name or "Mac"
        year = report.system.model_year or apple_model_year(model, report.system.product_sku)
        if year is not None:
            return f"{manufacturer} {product_name} ({year})".strip()
        base = f"{manufacturer} {product_name}".strip()
        return f"{base} ({model})" if model and model not in base else base
    base = " ".join(value for value in (manufacturer, product_name) if value)
    if not base:
        base = model if model and model != "inconnu" else report.system.processor
    return " ".join(base.split())


def _public_payload(report: PublicBenchmarkReport) -> dict[str, object]:
    """Préserve le contenu canonique des rapports publics historiques."""
    payload = report.model_dump(mode="json")
    system = payload["system"]
    assert isinstance(system, dict)
    if report.format_version == 1:
        for field in ("manufacturer", "commercial_name", "model_identifier"):
            system.pop(field, None)
    if report.format_version < 3:
        system.pop("product_sku", None)
    return payload


def _clean_product_sku(value: str | None, *, manufacturer: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    sku = _clean_public_text(value, field="product_sku", maximum=80)
    if re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        sku,
        re.IGNORECASE,
    ):
        raise ValueError("Un UUID ne peut pas être publié comme référence commerciale.")
    if (
        manufacturer
        and manufacturer.casefold() == "apple"
        and (not sku.upper().endswith("/A") or "XX/A" in sku.upper())
    ):
        raise ValueError(
            "La référence Apple doit être complète, se terminer par /A et ne pas "
            "contenir xx. N'indiquez jamais le numéro de série."
        )
    return sku


def _validate_public_result(result: PublicBenchmarkResult, *, campaign_repetitions: int) -> None:
    definition = CATALOG.get(result.benchmark_id)
    if definition is None:
        raise ValueError(f"Benchmark public inconnu : {result.benchmark_id}")
    if result.group != definition.group or result.name != definition.name:
        raise ValueError(f"Métadonnées incohérentes pour {result.benchmark_id}.")
    if result.unit != PUBLIC_RESULT_UNITS[result.benchmark_id] or not result.higher_is_better:
        raise ValueError(f"Unité ou sens incohérent pour {result.benchmark_id}.")
    if set(result.parameters) != PUBLIC_PARAMETERS_BY_BENCHMARK[result.benchmark_id]:
        raise ValueError(f"Paramètres incohérents pour {result.benchmark_id}.")
    if (
        result.repetitions != campaign_repetitions
        or len(result.sample_values) != result.repetitions
    ):
        raise ValueError(f"Nombre de passages incohérent pour {result.benchmark_id}.")
    if any(not math.isfinite(value) or value <= 0 for value in result.sample_values):
        raise ValueError(f"Échantillon invalide pour {result.benchmark_id}.")
    if not math.isclose(result.value, median(result.sample_values), rel_tol=1e-12):
        raise ValueError(f"Médiane incohérente pour {result.benchmark_id}.")
    minimum = min(result.sample_values)
    maximum = max(result.sample_values)
    if result.minimum is None or not math.isclose(result.minimum, minimum, rel_tol=1e-12):
        raise ValueError(f"Minimum incohérent pour {result.benchmark_id}.")
    if result.maximum is None or not math.isclose(result.maximum, maximum, rel_tol=1e-12):
        raise ValueError(f"Maximum incohérent pour {result.benchmark_id}.")
    spread = (maximum - minimum) / result.value * 100
    if result.relative_spread_percent is None or not math.isclose(
        result.relative_spread_percent,
        spread,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise ValueError(f"Dispersion incohérente pour {result.benchmark_id}.")
    for name, value in result.parameters.items():
        _clean_public_text(name, field="parameters", maximum=80)
        if isinstance(value, str):
            if _clean_public_text(value, field=f"parameters.{name}") != value:
                raise ValueError(f"Texte non canonique dans parameters.{name}.")
        elif not math.isfinite(value):
            raise ValueError(f"Paramètre non fini pour {result.benchmark_id}.")


def validate_public_report(report: PublicBenchmarkReport) -> PublicBenchmarkReport:
    """Valide le contenu et l'identifiant d'un rapport public déjà construit."""
    if not SUITE_VERSION_PATTERN.fullmatch(report.suite_version):
        raise ValueError("La version de la suite n'est pas reconnue.")
    if report.profile not in PROFILES:
        raise ValueError(f"Profil inconnu : {report.profile}")
    if report.system.operating_system not in {"Darwin", "Linux", "Windows"}:
        raise ValueError(f"Système inconnu : {report.system.operating_system}")
    if report.system.python_implementation != "CPython" or report.system.python_version != "3.14.4":
        raise ValueError("L'environnement Python ne correspond pas au protocole 0.3.0.")
    identity = (
        report.system.manufacturer,
        report.system.commercial_name,
        report.system.model_identifier,
    )
    if report.format_version == 1 and (
        report.source_schema_version not in {3, 4}
        or any(value is not None for value in identity)
        or report.system.product_sku is not None
    ):
        raise ValueError("Un rapport public v1 ne peut pas contenir l'identité commerciale.")
    if report.format_version == 2 and (
        report.source_schema_version == 6
        or report.system.product_sku is not None
        or report.system.commercial_name is None
        or report.system.model_identifier is None
    ):
        raise ValueError("Un rapport public v2 ne peut pas contenir de référence commerciale.")
    if report.format_version == 3 and (
        report.system.commercial_name is None or report.system.model_identifier is None
    ):
        raise ValueError("Un rapport public v3 doit identifier le modèle de la machine.")
    for field, value in (
        ("operating_system", report.system.operating_system),
        ("architecture", report.system.architecture),
        ("processor", report.system.processor),
        ("python_version", report.system.python_version),
        ("python_implementation", report.system.python_implementation),
    ):
        if _clean_public_text(value, field=field) != value:
            raise ValueError(f"Texte non canonique dans {field}.")
    for device in report.system.gpu_devices:
        if _clean_public_text(device, field="gpu_devices") != device:
            raise ValueError("Texte non canonique dans gpu_devices.")
    for field, value in (
        ("manufacturer", report.system.manufacturer),
        ("commercial_name", report.system.commercial_name),
        ("model_identifier", report.system.model_identifier),
    ):
        if value is not None and _clean_public_text(value, field=field) != value:
            raise ValueError(f"Texte non canonique dans {field}.")
    if (
        _clean_product_sku(
            report.system.product_sku,
            manufacturer=report.system.manufacturer,
        )
        != report.system.product_sku
    ):
        raise ValueError("Texte non canonique dans product_sku.")

    result_ids = [result.benchmark_id for result in report.results]
    if not result_ids or len(result_ids) != len(set(result_ids)):
        raise ValueError("Le rapport public doit contenir des résultats uniques.")
    if len(report.requested_benchmarks) != len(set(report.requested_benchmarks)):
        raise ValueError("Les benchmarks demandés doivent être uniques.")
    if len(report.failed_benchmarks) != len(set(report.failed_benchmarks)):
        raise ValueError("Les échecs doivent être uniques.")
    requested = set(report.requested_benchmarks)
    failures = set(report.failed_benchmarks)
    if requested - set(CATALOG) or failures - set(CATALOG):
        raise ValueError("Le rapport public contient un benchmark inconnu.")
    if set(result_ids) & failures or set(result_ids) | failures != requested:
        raise ValueError("Résultats et échecs incohérents avec les benchmarks demandés.")
    for result in report.results:
        _validate_public_result(result, campaign_repetitions=report.repetitions)

    content = _public_payload(report)
    content.pop("report_id")
    if report.report_id != _content_id(content):
        raise ValueError("L'identifiant ne correspond pas au contenu du rapport public.")
    return report


def load_public_report(
    path: Path | str,
    *,
    maximum_bytes: int = MAX_PUBLIC_REPORT_BYTES,
) -> PublicBenchmarkReport:
    """Charge un fichier public de taille bornée, puis valide tout son contenu."""
    source = Path(path)
    if source.stat().st_size > maximum_bytes:
        raise ValueError(f"Le rapport public dépasse la limite de {maximum_bytes} octets.")
    report = PublicBenchmarkReport.model_validate_json(source.read_text(encoding="utf-8"))
    return validate_public_report(report)


def public_report_to_benchmark_report(report: PublicBenchmarkReport) -> BenchmarkReport:
    """Adapte un rapport public validé au moteur de comparaison existant."""
    validate_public_report(report)
    results: list[BenchmarkResult] = []
    for result in report.results:
        definition = CATALOG[result.benchmark_id]
        documentation = BENCHMARK_DOCUMENTATION[result.benchmark_id]
        results.append(
            BenchmarkResult(
                benchmark_id=result.benchmark_id,
                group=result.group,
                name=result.name,
                description=definition.description,
                value=result.value,
                unit=result.unit,
                higher_is_better=result.higher_is_better,
                elapsed_seconds=1,
                parameters=result.parameters,
                methodology=documentation.methodology,
                limitations=documentation.limitations,
                references=[
                    REFERENCE_LIBRARY[reference_id] for reference_id in documentation.reference_ids
                ],
                repetitions=result.repetitions,
                sample_values=result.sample_values,
                minimum=result.minimum,
                maximum=result.maximum,
                relative_spread_percent=result.relative_spread_percent,
            )
        )

    return BenchmarkReport(
        schema_version=report.source_schema_version,
        suite_version=report.suite_version,
        protocol_version=report.protocol_version,
        recorded_at=datetime(1970, 1, 1, tzinfo=UTC),
        label=report.system.commercial_name or report.system.processor,
        profile=report.profile,
        repetitions=report.repetitions,
        requested_benchmarks=report.requested_benchmarks,
        system=SystemSnapshot(
            system=report.system.operating_system,
            release="rapport public",
            version="rapport public",
            machine=report.system.architecture,
            model=report.system.model_identifier or report.system.processor,
            manufacturer=report.system.manufacturer,
            product_name=report.system.commercial_name,
            model_year=apple_model_year(
                report.system.model_identifier or "",
                report.system.product_sku,
            ),
            product_sku=report.system.product_sku,
            processor=report.system.processor,
            physical_cpu_count=report.system.physical_cpu_count,
            logical_cpu_count=report.system.logical_cpu_count,
            memory_bytes=report.system.memory_bytes,
            gpu_devices=report.system.gpu_devices,
            python_version=report.system.python_version,
            python_implementation=report.system.python_implementation,
            python_executable="rapport public",
            disk_total_bytes=1,
            disk_free_bytes=0,
        ),
        results=results,
        failures=[
            BenchmarkFailure(
                benchmark_id=benchmark_id,
                message="Échec déclaré dans le rapport public.",
            )
            for benchmark_id in report.failed_benchmarks
        ],
    )


def export_public_report(
    report: BenchmarkReport,
    *,
    commercial_name: str | None = None,
    product_sku: str | None = None,
) -> PublicBenchmarkReport:
    """Reconstruit un rapport public depuis une liste blanche de champs."""
    if report.schema_version not in SUPPORTED_PRIVATE_SCHEMAS:
        raise ValueError(
            f"Le schéma privé {report.schema_version} ne peut pas être exporté sûrement."
        )
    protocol = report_protocol(report)
    if protocol != SUPPORTED_PROTOCOL:
        raise ValueError(f"Le protocole {protocol} ne peut pas être exporté sûrement.")
    if not report.results:
        raise ValueError("Un rapport sans résultat ne peut pas être exporté.")
    if not SUITE_VERSION_PATTERN.fullmatch(report.suite_version):
        raise ValueError("La version de la suite n'est pas reconnue.")
    if report.profile not in PROFILES:
        raise ValueError(f"Profil inconnu : {report.profile}")

    result_ids = [result.benchmark_id for result in report.results]
    if len(result_ids) != len(set(result_ids)):
        raise ValueError("Le rapport contient des résultats dupliqués.")
    unknown_requests = set(report.requested_benchmarks) - set(CATALOG)
    if unknown_requests:
        raise ValueError("Le rapport demande au moins un benchmark inconnu.")

    public_system = PublicSystemSnapshot(
        operating_system=_clean_public_text(report.system.system, field="operating_system"),
        architecture=_clean_public_text(report.system.machine, field="architecture"),
        manufacturer=(
            _clean_public_text(report.system.manufacturer, field="manufacturer")
            if report.system.manufacturer
            else ("Apple" if report.system.system == "Darwin" else None)
        ),
        commercial_name=_clean_public_text(
            commercial_name or suggest_public_machine_name(report),
            field="commercial_name",
        ),
        model_identifier=_clean_public_text(report.system.model, field="model_identifier"),
        product_sku=_clean_product_sku(
            report.system.product_sku if product_sku is None else product_sku,
            manufacturer=report.system.manufacturer
            or ("Apple" if report.system.system == "Darwin" else None),
        ),
        processor=_clean_public_text(report.system.processor, field="processor"),
        physical_cpu_count=report.system.physical_cpu_count,
        logical_cpu_count=report.system.logical_cpu_count,
        memory_bytes=report.system.memory_bytes,
        gpu_devices=[
            _clean_public_text(device, field="gpu_devices") for device in report.system.gpu_devices
        ],
        python_version=_clean_public_text(report.system.python_version, field="python_version"),
        python_implementation=_clean_public_text(
            report.system.python_implementation,
            field="python_implementation",
        ),
    )
    public_results = [_public_result(result) for result in report.results]
    failed = sorted({failure.benchmark_id for failure in report.failures})
    if any(benchmark_id not in CATALOG for benchmark_id in failed):
        raise ValueError("Le rapport contient l'échec d'un benchmark inconnu.")
    requested = set(report.requested_benchmarks)
    if set(result_ids) & set(failed) or set(result_ids) | set(failed) != requested:
        raise ValueError("Résultats et échecs incohérents avec les benchmarks demandés.")
    if any(result.repetitions != report.repetitions for result in report.results):
        raise ValueError("Nombre de passages incohérent dans les résultats.")

    content: dict[str, object] = {
        "format": "perfcomparator-public-report",
        "format_version": PUBLIC_FORMAT_VERSION,
        "license": PUBLIC_LICENSE,
        "verification": "community-unverified",
        "source_schema_version": report.schema_version,
        "suite_version": report.suite_version,
        "protocol_version": protocol,
        "profile": report.profile,
        "repetitions": report.repetitions,
        "requested_benchmarks": report.requested_benchmarks,
        "system": public_system.model_dump(mode="json"),
        "readiness_suitable": report.readiness.suitable if report.readiness else None,
        "results": [result.model_dump(mode="json") for result in public_results],
        "failed_benchmarks": failed,
    }
    public_report = PublicBenchmarkReport(report_id=_content_id(content), **content)
    return validate_public_report(public_report)


def save_public_report(report: PublicBenchmarkReport, path: Path | str) -> Path:
    """Écrit atomiquement un rapport public avec un ordre de champs stable."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    payload = json.dumps(
        _public_payload(report),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    temporary.write_text(payload + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination
