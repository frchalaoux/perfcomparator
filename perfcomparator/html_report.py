"""Génération d'un rapport HTML autonome, sans ressource externe."""

from __future__ import annotations

from html import escape

from .comparison import (
    CATEGORY_LABELS,
    REFERENCE_DURATIONS,
    SCENARIO_LABELS,
    ComparisonAnalysis,
    equivalent_duration,
    format_duration,
)


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _heat_color(index: float) -> str:
    difference = max(-50.0, min(50.0, index - 100))
    if abs(difference) < 2:
        return "#edf0f6"
    hue = 132 if difference > 0 else 4
    lightness = 92 - abs(difference) * 0.35
    return f"hsl({hue} 55% {lightness:.0f}%)"


def _bar_width(index: float, maximum: float) -> float:
    return max(2.0, min(100.0, index / maximum * 100))


def _machine_cards(analysis: ComparisonAnalysis) -> str:
    cards = []
    for machine in analysis.machines:
        difference = machine.overall_index - 100
        cards.append(
            "<article class='card'>"
            f"<h3>{_e(machine.label)}</h3>"
            f"<div class='big'>{machine.overall_index:.0f}</div>"
            f"<p>Indice global personnalisé · {difference:+.1f} %</p>"
            f"<small>{_e(machine.report.system.processor)} · "
            f"{_e(machine.report.system.memory_bytes // 1_073_741_824 if machine.report.system.memory_bytes else '?')} Gio</small>"
            "</article>"
        )
    return "".join(cards)


def _scenario_bars(analysis: ComparisonAnalysis) -> str:
    maximum = max(
        machine.scenarios.get(scenario, 100)
        for scenario in analysis.scenario_weights
        for machine in analysis.machines
    )
    rows = []
    for scenario in analysis.scenario_weights:
        rows.append(f"<section class='scenario'><h3>{_e(SCENARIO_LABELS[scenario])}</h3>")
        for machine in analysis.machines:
            index = machine.scenarios[scenario]
            rows.append(
                "<div class='bar-row'>"
                f"<span>{_e(machine.label)}</span>"
                "<div class='bar-track'>"
                f"<div class='bar' style='width:{_bar_width(index, maximum):.1f}%'></div>"
                "</div>"
                f"<strong>{index:.0f}</strong>"
                "</div>"
            )
        rows.append("</section>")
    return "".join(rows)


def _category_bars(analysis: ComparisonAnalysis) -> str:
    groups = tuple(analysis.machines[0].categories)
    maximum = max(machine.categories[group] for group in groups for machine in analysis.machines)
    rows = []
    for group in groups:
        rows.append(f"<section class='scenario'><h3>{_e(CATEGORY_LABELS.get(group, group))}</h3>")
        for machine in analysis.machines:
            index = machine.categories[group]
            rows.append(
                "<div class='bar-row'>"
                f"<span>{_e(machine.label)}</span>"
                "<div class='bar-track'>"
                f"<div class='bar secondary' style='width:{_bar_width(index, maximum):.1f}%'></div>"
                "</div>"
                f"<strong>{index:.0f}</strong>"
                "</div>"
            )
        rows.append("</section>")
    return "".join(rows)


def _heatmap(analysis: ComparisonAnalysis) -> str:
    headers = "".join(f"<th>{_e(machine.label)}</th>" for machine in analysis.machines)
    rows = []
    for scenario in analysis.scenario_weights:
        cells = "".join(
            f"<td style='background:{_heat_color(machine.scenarios[scenario])}'>"
            f"{machine.scenarios[scenario]:.0f}</td>"
            for machine in analysis.machines
        )
        rows.append(f"<tr><th>{_e(SCENARIO_LABELS[scenario])}</th>{cells}</tr>")
    return f"<table><thead><tr><th>Scénario</th>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _timelines(analysis: ComparisonAnalysis) -> str:
    sections = []
    for scenario in analysis.scenario_weights:
        headers = "".join(f"<th>{_e(machine.label)}</th>" for machine in analysis.machines)
        rows = []
        for duration in REFERENCE_DURATIONS:
            cells = []
            for machine in analysis.machines:
                equivalent = equivalent_duration(duration, machine.scenarios[scenario])
                delta = duration - equivalent
                if abs(delta) < 0.5:
                    delta_label = "référence"
                elif delta > 0:
                    delta_label = f"{format_duration(delta)} gagnées"
                else:
                    delta_label = f"{format_duration(abs(delta))} supplémentaires"
                cells.append(
                    f"<td><strong>{_e(format_duration(equivalent))}</strong>"
                    f"<small class='time-delta'>{_e(delta_label)}</small></td>"
                )
            rows.append(f"<tr><th>{_e(format_duration(duration))}</th>{''.join(cells)}</tr>")
        sections.append(
            f"<section class='timeline'><h3>{_e(SCENARIO_LABELS[scenario])}</h3>"
            f"<table><thead><tr><th>Temps sur la référence</th>{headers}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></section>"
        )
    return "".join(sections)


def _dumbbell(analysis: ComparisonAnalysis, benchmark_id: str) -> str:
    if len(analysis.machines) != 2:
        return ""
    first, second = analysis.machines
    first_index = first.metrics[benchmark_id].index
    second_index = second.metrics[benchmark_id].index
    scale_max = max(120.0, first_index, second_index) * 1.1
    first_x = 20 + first_index / scale_max * 260
    second_x = 20 + second_index / scale_max * 260
    return (
        "<svg class='dumbbell' viewBox='0 0 300 34' role='img' "
        f"aria-label='Écart entre {_e(first.label)} et {_e(second.label)}'>"
        f"<line x1='{first_x:.1f}' y1='17' x2='{second_x:.1f}' y2='17' />"
        f"<circle class='baseline' cx='{first_x:.1f}' cy='17' r='7' />"
        f"<circle class='candidate' cx='{second_x:.1f}' cy='17' r='7' />"
        "</svg>"
    )


def _benchmark_details(analysis: ComparisonAnalysis) -> str:
    sections = []
    maximum = max(
        machine.metrics[benchmark_id].index
        for benchmark_id in analysis.common_benchmarks
        for machine in analysis.machines
    )
    for benchmark_id in analysis.common_benchmarks:
        rows = []
        for machine in analysis.machines:
            metric = machine.metrics[benchmark_id]
            spread = (
                "dispersion indisponible"
                if metric.spread_percent is None
                else f"dispersion {metric.spread_percent:.1f} %"
            )
            rows.append(
                "<div class='metric-row'>"
                f"<span>{_e(machine.label)}</span>"
                "<div class='bar-track'><div class='bar secondary' "
                f"style='width:{_bar_width(metric.index, maximum):.1f}%'></div></div>"
                f"<strong>{metric.index:.0f}</strong>"
                f"<small>{metric.value:.2f} {_e(metric.unit)} · {_e(spread)}</small>"
                "</div>"
            )
        candidate_notes = "".join(
            f"<li><strong>{_e(machine.label)}</strong> : "
            f"{machine.metrics[benchmark_id].difference_percent:+.1f} % — "
            f"{_e(machine.metrics[benchmark_id].conclusion)} ; "
            f"{_e(machine.metrics[benchmark_id].uncertainty)}</li>"
            for machine in analysis.machines[1:]
        )
        sections.append(
            "<details>"
            f"<summary>{_e(analysis.machines[0].metrics[benchmark_id].name)} "
            f"<code>{_e(benchmark_id)}</code></summary>"
            f"{_dumbbell(analysis, benchmark_id)}{''.join(rows)}<ul>{candidate_notes}</ul>"
            "</details>"
        )
    return "".join(sections)


def render_html(analysis: ComparisonAnalysis) -> str:
    """Retourne un document HTML complet et portable."""
    warnings = "".join(f"<li>{_e(item)}</li>" for item in analysis.warnings)
    narratives = "".join(
        f"<p><strong>{_e(machine.label)}.</strong> {_e(machine.narrative)}</p>"
        for machine in analysis.machines[1:]
    )
    weights = " · ".join(
        f"{SCENARIO_LABELS[scenario]} {weight * 100:.0f} %"
        for scenario, weight in analysis.scenario_weights.items()
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comparaison PerfComparator</title>
<style>
:root {{ --ink:#172033; --muted:#667085; --paper:#f6f7fb; --accent:#315efb; --accent2:#19a974; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,sans-serif; color:var(--ink); background:var(--paper); line-height:1.5; }}
main {{ max-width:1180px; margin:auto; padding:32px 20px 64px; }}
h1 {{ font-size:clamp(2rem,5vw,4rem); line-height:1; margin-bottom:8px; }}
h2 {{ margin-top:48px; }}
.lead,.muted,small {{ color:var(--muted); }}
.time-delta {{ display:block; margin-top:3px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; }}
.card,.scenario,.timeline,details,.notice {{ background:white; border:1px solid #e2e5ee; border-radius:14px; padding:18px; box-shadow:0 5px 18px #18203b0c; }}
.big {{ font-size:3rem; font-weight:800; color:var(--accent); }}
.scenario,.timeline,details {{ margin:12px 0; }}
.bar-row,.metric-row {{ display:grid; grid-template-columns:minmax(130px,1fr) minmax(180px,4fr) 60px; gap:12px; align-items:center; margin:9px 0; }}
.metric-row {{ grid-template-columns:minmax(130px,1fr) minmax(180px,4fr) 60px minmax(180px,2fr); }}
.bar-track {{ height:14px; background:#edf0f6; border-radius:999px; overflow:hidden; }}
.bar {{ height:100%; background:linear-gradient(90deg,var(--accent),#7892ff); border-radius:inherit; }}
.bar.secondary {{ background:linear-gradient(90deg,var(--accent2),#65d6a8); }}
table {{ border-collapse:collapse; width:100%; background:white; }}
th,td {{ padding:11px; border:1px solid #dfe3ec; text-align:right; }}
th:first-child {{ text-align:left; }}
details summary {{ cursor:pointer; font-weight:700; }}
.dumbbell {{ width:300px; max-width:100%; display:block; margin:10px 0; }}
.dumbbell line {{ stroke:#9aa4b5; stroke-width:4; }}
.dumbbell .baseline {{ fill:#315efb; }} .dumbbell .candidate {{ fill:#19a974; }}
code {{ color:#45506a; }}
@media (max-width:700px) {{ .metric-row,.bar-row {{ grid-template-columns:1fr 2fr 52px; }} .metric-row small {{ grid-column:1/-1; }} }}
@media print {{ body {{ background:white; }} .card,.scenario,.timeline,details,.notice {{ box-shadow:none; break-inside:avoid; }} }}
</style>
</head>
<body><main>
<header><p class="muted">PerfComparator · rapport autonome</p><h1>Ce que ces performances changent au quotidien</h1>
<p class="lead">Référence : <strong>{_e(analysis.baseline_label)}</strong>, ramenée à l'indice 100. Les temps sont des équivalences relatives, pas des durées applicatives observées.</p></header>
<section class="cards">{_machine_cards(analysis)}</section>
<section><h2>Lecture en langage courant</h2>{narratives}<div class="notice"><strong>Pondération :</strong> {_e(weights)}<ul>{warnings}</ul></div></section>
<section><h2>Catégories techniques</h2>{_category_bars(analysis)}</section>
<section><h2>Scénarios d'usage</h2>{_scenario_bars(analysis)}</section>
<section><h2>Carte thermique</h2><p class="muted">100 égale la référence ; vert signifie plus rapide, rouge plus lent.</p>{_heatmap(analysis)}</section>
<section><h2>Temps équivalents</h2><p class="muted">Durée théorique pour accomplir une quantité de travail identique à la référence.</p>{_timelines(analysis)}</section>
<section><h2>Benchmarks détaillés</h2>{_benchmark_details(analysis)}</section>
<footer><h2>Précautions</h2><p>Comparer au moins trois passages réalisés avec le même profil, la même version de la suite et la même version de Python. Une plage min–max chevauchante est présentée comme non concluante. Les seuils qualitatifs sont des aides de lecture, pas des lois de perception.</p></footer>
</main></body></html>"""
