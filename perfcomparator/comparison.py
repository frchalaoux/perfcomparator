"""Analyse humaine de deux rapports ou plus, indépendante du rendu."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .models import BenchmarkReport, BenchmarkResult

SCENARIOS: dict[str, dict[str, float]] = {
    "quotidien": {
        "cpu.integer": 0.25,
        "cpu.float": 0.10,
        "application.json": 0.25,
        "application.sqlite": 0.25,
        "storage.random-read": 0.15,
    },
    "developpement": {
        "cpu.integer": 0.15,
        "cpu.multicore": 0.25,
        "cpu.compression": 0.10,
        "memory.copy": 0.10,
        "storage.random-read": 0.15,
        "storage.random-write": 0.10,
        "application.sqlite": 0.15,
    },
    "calcul-intensif": {
        "cpu.float": 0.15,
        "cpu.multicore": 0.20,
        "memory.copy": 0.15,
        "cpu.hash": 0.10,
        "gpu.compute-fp32": 0.40,
    },
    "fichiers": {
        "cpu.hash": 0.15,
        "cpu.compression": 0.25,
        "storage.read": 0.20,
        "storage.write": 0.20,
        "storage.random-read": 0.10,
        "storage.random-write": 0.10,
    },
    "base-de-donnees": {
        "application.sqlite": 0.40,
        "memory.copy": 0.15,
        "storage.random-read": 0.25,
        "storage.random-write": 0.20,
    },
    "creation": {
        "cpu.float": 0.10,
        "cpu.multicore": 0.15,
        "memory.copy": 0.10,
        "storage.read": 0.10,
        "storage.write": 0.10,
        "gpu.image-filter": 0.25,
        "gpu.raster": 0.20,
    },
    "jeu-3d": {
        "gpu.raster": 0.55,
        "gpu.memory": 0.20,
        "gpu.compute-fp32": 0.15,
        "memory.copy": 0.10,
    },
}

SCENARIO_LABELS = {
    "quotidien": "Réactivité quotidienne",
    "developpement": "Développement",
    "calcul-intensif": "Calcul intensif",
    "fichiers": "Gestion de fichiers",
    "base-de-donnees": "Base de données locale",
    "creation": "Création 3D/vidéo",
    "jeu-3d": "Jeu et rendu 3D généraliste",
}

CATEGORY_LABELS = {
    "application": "Applications",
    "cpu": "Processeur",
    "memory": "Mémoire",
    "storage": "Stockage",
    "gpu": "Processeur graphique",
}

REFERENCE_DURATIONS = (10, 120, 1_800, 14_400)
MACHINE_DEPENDENT_PARAMETERS = {
    "cpu.multicore": frozenset({"workers"}),
    "gpu.compute-fp32": frozenset(
        {"gpu_index", "gpu_device", "gpu_backend", "gpu_adapter_type", "wgpu_version"}
    ),
    "gpu.memory": frozenset(
        {"gpu_index", "gpu_device", "gpu_backend", "gpu_adapter_type", "wgpu_version"}
    ),
    "gpu.image-filter": frozenset(
        {"gpu_index", "gpu_device", "gpu_backend", "gpu_adapter_type", "wgpu_version"}
    ),
    "gpu.raster": frozenset(
        {"gpu_index", "gpu_device", "gpu_backend", "gpu_adapter_type", "wgpu_version"}
    ),
}


@dataclass(frozen=True)
class MetricComparison:
    """Écart d'une machine avec la référence pour un benchmark."""

    benchmark_id: str
    name: str
    group: str
    value: float
    unit: str
    index: float
    difference_percent: float
    conclusion: str
    uncertainty: str
    spread_percent: float | None


@dataclass(frozen=True)
class MachineAnalysis:
    """Indices techniques et humains d'une machine."""

    label: str
    report: BenchmarkReport
    metrics: dict[str, MetricComparison]
    categories: dict[str, float]
    scenarios: dict[str, float]
    overall_index: float
    narrative: str


@dataclass(frozen=True)
class ComparisonAnalysis:
    """Analyse complète prête pour la console ou le HTML."""

    baseline_label: str
    machines: tuple[MachineAnalysis, ...]
    common_benchmarks: tuple[str, ...]
    scenario_weights: dict[str, float]
    warnings: tuple[str, ...]


LEGACY_PROTOCOL_BY_SUITE_VERSION = {
    version: "0.3.0" for version in ("0.3.0.dev1", "0.3.0.dev2", "0.3.0", "0.3.1.dev0", "0.3.1")
}


def report_label(report: BenchmarkReport) -> str:
    return report.label or report.system.model


def comparison_protocol(version: str) -> str:
    """Retrouve le protocole des anciens rapports qui ne l'enregistraient pas."""
    return LEGACY_PROTOCOL_BY_SUITE_VERSION.get(version, version)


def report_protocol(report: BenchmarkReport) -> str:
    """Retourne le protocole déclaré, ou le protocole historique de la suite."""
    return report.protocol_version or comparison_protocol(report.suite_version)


def validate_reports(reports: list[BenchmarkReport]) -> None:
    """Refuse les comparaisons dont le protocole n'est pas homogène."""
    if len(reports) < 2:
        raise ValueError("Indiquez au moins deux rapports.")
    reference = reports[0]
    for report in reports[1:]:
        if report_protocol(report) != report_protocol(reference):
            raise ValueError("Les rapports doivent utiliser des versions compatibles de la suite.")
        if report.profile != reference.profile:
            raise ValueError("Les rapports doivent utiliser le même profil.")
        if report.system.python_version != reference.system.python_version:
            raise ValueError("Les rapports doivent utiliser la même version de Python.")
        if report.system.python_implementation != reference.system.python_implementation:
            raise ValueError("Les rapports doivent utiliser la même implémentation de Python.")
        schema_pair = {report.schema_version, reference.schema_version}
        if report.schema_version != reference.schema_version and schema_pair != {6, 7}:
            raise ValueError("Les rapports doivent utiliser le même schéma JSON.")


def parse_scenario_weights(values: list[str] | None) -> dict[str, float]:
    """Convertit `scenario=poids` et normalise la somme à un."""
    if not values:
        equal = 1 / len(SCENARIOS)
        return {scenario: equal for scenario in SCENARIOS}
    weights: dict[str, float] = {}
    for value in values:
        try:
            scenario, raw_weight = value.split("=", 1)
            weight = float(raw_weight)
        except ValueError as error:
            raise ValueError(
                f"Poids invalide : {value!r}; format attendu scenario=nombre."
            ) from error
        if scenario not in SCENARIOS:
            raise ValueError(f"Scénario inconnu : {scenario}")
        if weight < 0:
            raise ValueError("Les poids doivent être positifs ou nuls.")
        weights[scenario] = weight
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("La somme des poids doit être supérieure à zéro.")
    return {scenario: weight / total for scenario, weight in weights.items()}


def performance_ratio(result: BenchmarkResult, baseline: BenchmarkResult) -> float:
    """Retourne un rapport où une valeur supérieure signifie toujours mieux."""
    if result.higher_is_better != baseline.higher_is_better:
        raise ValueError(f"Sens de métrique incohérent pour {result.benchmark_id}.")
    if result.unit != baseline.unit:
        raise ValueError(f"Unité incohérente pour {result.benchmark_id}.")
    ignored = MACHINE_DEPENDENT_PARAMETERS.get(result.benchmark_id, frozenset())
    result_parameters = {
        name: value for name, value in result.parameters.items() if name not in ignored
    }
    baseline_parameters = {
        name: value for name, value in baseline.parameters.items() if name not in ignored
    }
    if result_parameters != baseline_parameters:
        raise ValueError(f"Paramètres incohérents pour {result.benchmark_id}.")
    if result.higher_is_better:
        return result.value / baseline.value
    return baseline.value / result.value


def difference_label(difference_percent: float, *, inconclusive: bool) -> str:
    """Traduit un écart numérique en formulation prudente."""
    if inconclusive:
        return "différence non concluante"
    magnitude = abs(difference_percent)
    if magnitude < 5:
        return "sensiblement équivalent"
    if magnitude < 15:
        strength = "différence légère"
    elif magnitude < 30:
        strength = "différence nette"
    elif magnitude < 60:
        strength = "différence importante"
    else:
        strength = "changement de catégorie"
    direction = "en faveur de cette machine" if difference_percent > 0 else "en sa défaveur"
    return f"{strength} {direction}"


def _bounds(result: BenchmarkResult) -> tuple[float, float]:
    return result.minimum or result.value, result.maximum or result.value


def _uncertainty(result: BenchmarkResult, baseline: BenchmarkResult) -> tuple[bool, str]:
    if result.repetitions < 2 or baseline.repetitions < 2:
        return False, "incertitude non estimée (un seul passage)"
    result_low, result_high = _bounds(result)
    baseline_low, baseline_high = _bounds(baseline)
    overlaps = max(result_low, baseline_low) <= min(result_high, baseline_high)
    if overlaps:
        return True, "plages min–max chevauchantes"
    return False, "plages min–max séparées"


def _geometric_mean(values: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in values)
    if not values or total_weight <= 0:
        return 1.0
    return math.exp(sum(weight * math.log(value) for value, weight in values) / total_weight)


def _scenario_index(ratios: dict[str, float], weights: dict[str, float]) -> float:
    available = [
        (ratios[benchmark_id], weight)
        for benchmark_id, weight in weights.items()
        if benchmark_id in ratios
    ]
    return _geometric_mean(available) * 100


def format_duration(seconds: float) -> str:
    """Formate une durée avec une précision adaptée à l'expérience humaine."""
    if seconds < 60:
        return f"{seconds:.1f} s"
    rounded = round(seconds)
    hours, remainder = divmod(rounded, 3_600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes} min {secs:02d} s"


def equivalent_duration(reference_seconds: float, index: float) -> float:
    return reference_seconds / (index / 100)


def _narrative(label: str, scenarios: dict[str, float]) -> str:
    if not scenarios:
        return f"{label} ne partage aucun scénario complet avec la référence."
    best_name, best_index = max(scenarios.items(), key=lambda item: item[1])
    worst_name, worst_index = min(scenarios.items(), key=lambda item: item[1])
    best_duration = equivalent_duration(3_600, best_index)
    time_delta = 3_600 - best_duration
    time_phrase = (
        f"{format_duration(abs(time_delta))} gagnées"
        if time_delta >= 0
        else f"{format_duration(abs(time_delta))} supplémentaires"
    )
    sentence = (
        f"{label} obtient son meilleur résultat relatif en {SCENARIO_LABELS[best_name].lower()} "
        f"({best_index - 100:+.0f} %), soit {format_duration(best_duration)} pour une charge "
        f"équivalente à une heure sur la référence ({time_phrase})."
    )
    if worst_index < 100:
        sentence += (
            f" Son point le moins favorable est {SCENARIO_LABELS[worst_name].lower()} "
            f"({worst_index - 100:+.0f} %)."
        )
    return sentence


def analyze_reports(
    reports: list[BenchmarkReport], scenario_weights: dict[str, float]
) -> ComparisonAnalysis:
    """Construit indices, scénarios, incertitudes et résumés narratifs."""
    validate_reports(reports)
    maps = [{result.benchmark_id: result for result in report.results} for report in reports]
    common = tuple(sorted(set(maps[0]).intersection(*(set(items) for items in maps[1:]))))
    if not common:
        raise ValueError("Les rapports ne partagent aucun benchmark.")
    active_weights = {
        scenario: weight
        for scenario, weight in scenario_weights.items()
        if any(benchmark_id in common for benchmark_id in SCENARIOS[scenario])
    }
    active_total = sum(active_weights.values())
    if active_total <= 0:
        raise ValueError("Les rapports ne couvrent aucun scénario pondéré.")
    active_weights = {
        scenario: weight / active_total for scenario, weight in active_weights.items()
    }
    baseline_map = maps[0]
    machines: list[MachineAnalysis] = []
    warnings: list[str] = []
    suite_versions = sorted({report.suite_version for report in reports})
    if len(suite_versions) > 1:
        warnings.append(
            f"Versions compatibles du protocole {report_protocol(reports[0])} comparées : "
            + ", ".join(suite_versions)
            + "."
        )
    for report in reports:
        warnings.extend(
            f"{report_label(report)} : {warning}" for warning in report.environment_warnings
        )
        if report.readiness is not None:
            warnings.extend(
                f"{report_label(report)}, état initial : {warning}"
                for warning in report.readiness.warnings
            )
    if any(report.repetitions < 3 for report in reports):
        warnings.append("Moins de trois passages : la dispersion est peu représentative.")
    union = set().union(*(set(items) for items in maps))
    if len(common) != len(union):
        warnings.append(
            f"La comparaison utilise seulement {len(common)} benchmark(s) commun(s) sur "
            f"{len(union)} présent(s) dans les rapports."
        )
    if "cpu.multicore" in common:
        worker_counts = [items["cpu.multicore"].parameters.get("workers") for items in maps]
        if len(set(worker_counts)) > 1:
            details = ", ".join(
                f"{report_label(report)} : {workers} processus"
                for report, workers in zip(reports, worker_counts, strict=True)
            )
            warnings.append(
                "cpu.multicore mesure le débit total avec le parallélisme propre à chaque "
                f"machine ({details})."
            )
    for report in reports:
        unstable = [
            result
            for result in report.results
            if result.relative_spread_percent is not None and result.relative_spread_percent > 15
        ]
        if unstable:
            warnings.append(
                f"{report_label(report)} : {len(unstable)} benchmark(s) dépassent 15 % "
                "de dispersion ; répéter la campagne dans des conditions plus stables."
            )
    ignored_scenarios = set(scenario_weights) - set(active_weights)
    if ignored_scenarios:
        warnings.append(
            "Scénarios ignorés faute de benchmarks communs : "
            + ", ".join(SCENARIO_LABELS[item] for item in sorted(ignored_scenarios))
            + "."
        )
    for scenario in active_weights:
        missing = set(SCENARIOS[scenario]) - set(common)
        if missing:
            warnings.append(
                f"{SCENARIO_LABELS[scenario]} est calculé partiellement ; absents : "
                + ", ".join(sorted(missing))
                + "."
            )
    for report, result_map in zip(reports, maps, strict=True):
        metrics: dict[str, MetricComparison] = {}
        ratios: dict[str, float] = {}
        for benchmark_id in common:
            result = result_map[benchmark_id]
            baseline = baseline_map[benchmark_id]
            ratio = performance_ratio(result, baseline)
            ratios[benchmark_id] = ratio
            inconclusive, uncertainty = _uncertainty(result, baseline)
            difference = (ratio - 1) * 100
            metrics[benchmark_id] = MetricComparison(
                benchmark_id=benchmark_id,
                name=result.name,
                group=result.group,
                value=result.value,
                unit=result.unit,
                index=ratio * 100,
                difference_percent=difference,
                conclusion=difference_label(difference, inconclusive=inconclusive),
                uncertainty=uncertainty,
                spread_percent=result.relative_spread_percent,
            )
        categories = {
            group: _geometric_mean(
                [
                    (ratio, 1.0)
                    for benchmark_id, ratio in ratios.items()
                    if result_map[benchmark_id].group == group
                ]
            )
            * 100
            for group in sorted({result_map[benchmark_id].group for benchmark_id in common})
        }
        scenarios = {
            scenario: _scenario_index(ratios, weights)
            for scenario, weights in SCENARIOS.items()
            if scenario in active_weights
        }
        overall = (
            _geometric_mean(
                [
                    (scenarios[scenario] / 100, weight)
                    for scenario, weight in active_weights.items()
                    if scenario in scenarios
                ]
            )
            * 100
        )
        label = report_label(report)
        machines.append(
            MachineAnalysis(
                label=label,
                report=report,
                metrics=metrics,
                categories=categories,
                scenarios=scenarios,
                overall_index=overall,
                narrative=_narrative(label, scenarios),
            )
        )
    return ComparisonAnalysis(
        baseline_label=report_label(reports[0]),
        machines=tuple(machines),
        common_benchmarks=common,
        scenario_weights=active_weights,
        warnings=tuple(warnings),
    )
