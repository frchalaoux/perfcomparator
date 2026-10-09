from pathlib import Path

from test_repository import sample_report
from typer.testing import CliRunner

from perfcomparator import __version__
from perfcomparator.cli import app
from perfcomparator.contribution import ContributionResult
from perfcomparator.public_report import export_public_report, save_public_report
from perfcomparator.repository import JsonReportRepository

runner = CliRunner()


def test_version_option_displays_installed_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"PerfComparator {__version__}"


def test_list_displays_groups_profiles_and_individual_benchmarks() -> None:
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "GROUPES" in result.stdout
    assert "thorough" in result.stdout
    assert "cpu.integer" in result.stdout
    assert "storage.random-write" in result.stdout
    assert "gpu.compute-fp32" in result.stdout
    assert "gpu.raster" in result.stdout


def test_history_is_empty_in_an_isolated_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["history"])

    assert result.exit_code == 0
    assert "Aucun benchmark archivé" in result.stdout


def test_describe_displays_method_limits_and_references() -> None:
    result = runner.invoke(app, ["describe", "cpu.hash"])

    assert result.exit_code == 0
    assert "Méthode" in result.stdout
    assert "Limites" in result.stdout
    assert "FIPS PUB 180-4" in result.stdout


def test_compare_uses_first_report_as_baseline(tmp_path: Path) -> None:
    first = JsonReportRepository(tmp_path / "first").save(sample_report())
    second = JsonReportRepository(tmp_path / "second").save(
        sample_report(value=15, label="PC test")
    )

    result = runner.invoke(app, ["compare", str(first), str(second)])

    assert result.exit_code == 0
    assert "Mac test" in result.stdout
    assert "PC test" in result.stdout
    assert "+50.0 %" in result.stdout


def test_compare_displays_a_conclusion_for_each_candidate(tmp_path: Path) -> None:
    baseline = JsonReportRepository(tmp_path / "baseline").save(sample_report())
    faster = JsonReportRepository(tmp_path / "faster").save(
        sample_report(value=15, label="PC rapide")
    )
    slower = JsonReportRepository(tmp_path / "slower").save(sample_report(value=8, label="PC lent"))

    result = runner.invoke(app, ["compare", str(baseline), str(faster), str(slower)])

    assert result.exit_code == 0
    assert "Mac test 100 (référence)" in result.stdout
    assert "PC rapide 150 (+50.0 % ; différence importante en faveur de cette machine)" in (
        result.stdout
    )
    assert "PC lent 80 (-20.0 % ; différence nette en sa défaveur)" in result.stdout


def test_compare_writes_a_weighted_autonomous_html_report(tmp_path: Path) -> None:
    first = JsonReportRepository(tmp_path / "first").save(sample_report())
    second = JsonReportRepository(tmp_path / "second").save(
        sample_report(value=12, label="PC test")
    )
    output = tmp_path / "comparaison.html"

    result = runner.invoke(
        app,
        [
            "compare",
            str(first),
            str(second),
            "--weight",
            "quotidien=1",
            "--html",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "Rapport HTML" in result.stdout
    assert output.exists()
    assert "Carte thermique" in output.read_text(encoding="utf-8")


def test_compare_accepts_a_downloaded_public_report(tmp_path: Path) -> None:
    baseline_report = sample_report().model_copy(
        update={"suite_version": "0.4.0.dev1", "protocol_version": "0.3.0"}
    )
    baseline_report.results[0].parameters = {"workers": 1}
    baseline_report.results[0].sample_values = [10]
    baseline_report.results[0].minimum = 10
    baseline_report.results[0].maximum = 10
    baseline_report.results[0].relative_spread_percent = 0
    baseline = JsonReportRepository(tmp_path / "baseline").save(baseline_report)

    candidate_report = baseline_report.model_copy(deep=True)
    candidate_report.results[0].value = 15
    candidate_report.results[0].sample_values = [15]
    candidate_report.results[0].minimum = 15
    candidate_report.results[0].maximum = 15
    public = save_public_report(
        export_public_report(candidate_report),
        tmp_path / "downloaded-public.json",
    )

    result = runner.invoke(app, ["compare", str(baseline), str(public)])

    assert result.exit_code == 0
    assert "Mac test" in result.stdout
    assert "Apple MacBook Pro (Mac16,1)" in result.stdout
    assert "+50.0 %" in result.stdout


def test_export_public_requires_explicit_license_acceptance(tmp_path: Path) -> None:
    report = sample_report().model_copy(
        update={"suite_version": "0.4.0.dev0", "protocol_version": "0.3.0"}
    )
    report.results[0].parameters = {"workers": 1}
    report.results[0].sample_values = [10]
    report.results[0].minimum = 10
    report.results[0].maximum = 10
    report.results[0].relative_spread_percent = 0
    source = JsonReportRepository(tmp_path / "private").save(report)

    result = runner.invoke(
        app,
        ["export-public", str(source), "--output", str(tmp_path / "public.json")],
    )

    assert result.exit_code == 2
    assert "--accept-cc0" in result.output
    assert not (tmp_path / "public.json").exists()


def test_export_public_writes_only_the_requested_local_file(tmp_path: Path) -> None:
    report = sample_report(label="Private label").model_copy(
        update={"suite_version": "0.4.0.dev0", "protocol_version": "0.3.0"}
    )
    report.results[0].parameters = {"workers": 1}
    report.results[0].sample_values = [10]
    report.results[0].minimum = 10
    report.results[0].maximum = 10
    report.results[0].relative_spread_percent = 0
    source = JsonReportRepository(tmp_path / "private").save(report)
    output = tmp_path / "exports" / "public.json"

    result = runner.invoke(
        app,
        [
            "export-public",
            str(source),
            "--output",
            str(output),
            "--accept-cc0",
        ],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "Private label" not in output.read_text(encoding="utf-8")
    assert "CC0-1.0" in result.stdout

    validation = runner.invoke(app, ["validate-public", str(output)])

    assert validation.exit_code == 0
    assert "Rapport public valide" in validation.stdout
    assert "performances non certifiées" in validation.stdout


def test_contribute_guides_a_user_without_exposing_the_private_report(
    tmp_path: Path, monkeypatch
) -> None:
    report = sample_report(label="Private contribution label").model_copy(
        update={"suite_version": "0.4.0.dev2", "protocol_version": "0.3.0"}
    )
    report.results[0].parameters = {"workers": 1}
    report.results[0].sample_values = [10]
    report.results[0].minimum = 10
    report.results[0].maximum = 10
    report.results[0].relative_spread_percent = 0
    private = JsonReportRepository(tmp_path / "private").save(report)
    submitted = {}

    def fake_submit(public_report, public_path, *, gh, login):
        submitted["report"] = public_report
        submitted["payload"] = public_path.read_text(encoding="utf-8")
        submitted["gh"] = gh
        submitted["login"] = login
        return ContributionResult(
            pull_request_url="https://github.com/example/pr/1",
            branch="add/report-test",
            fork="alice/perfcomparator-results",
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("perfcomparator.cli.github_cli_path", lambda: Path("/fake/gh"))
    monkeypatch.setattr("perfcomparator.cli.github_login", lambda _gh: "alice")
    monkeypatch.setattr("perfcomparator.cli.submit_public_report", fake_submit)

    result = runner.invoke(
        app,
        ["contribute", str(private)],
        input="y\nApple MacBook Pro 15 pouces (2018)\nMR942FN/A\ny\ny\n",
    )

    assert result.exit_code == 0
    assert "ajoutez l'année de commercialisation si vous la connaissez" in result.stdout
    assert "APERÇU PUBLIC" in result.stdout
    assert "Contribution envoyée" in result.stdout
    assert "https://github.com/example/pr/1" in result.stdout
    assert submitted["login"] == "alice"
    assert submitted["report"].system.commercial_name == ("Apple MacBook Pro 15 pouces (2018)")
    assert submitted["report"].system.product_sku == "MR942FN/A"
    assert "Private contribution label" not in submitted["payload"]
    assert list((tmp_path / "data" / "public").glob("*.json"))


def test_contribute_dry_run_never_connects_to_github(tmp_path: Path, monkeypatch) -> None:
    report = sample_report().model_copy(
        update={
            "schema_version": 3,
            "suite_version": "0.3.0.dev2",
            "protocol_version": None,
            "readiness": None,
        }
    )
    report.results[0].parameters = {"workers": 1}
    report.results[0].sample_values = [10]
    report.results[0].minimum = 10
    report.results[0].maximum = 10
    report.results[0].relative_spread_percent = 0
    private = JsonReportRepository(tmp_path / "private").save(report)
    monkeypatch.chdir(tmp_path)

    def unexpected_github_call():
        raise AssertionError("GitHub ne doit pas être consulté pendant un essai local.")

    monkeypatch.setattr("perfcomparator.cli.github_cli_path", unexpected_github_call)

    result = runner.invoke(
        app,
        ["contribute", str(private), "--dry-run"],
        input="y\n\n\ny\n",
    )

    assert result.exit_code == 0
    assert "Essai local terminé" in result.stdout
    assert "aucune connexion ni opération GitHub" in result.stdout
