from pathlib import Path

from test_public_report import exportable_report

from perfcomparator import contribution
from perfcomparator.public_report import export_public_report, save_public_report


def test_catalog_owner_uses_the_main_repository_without_creating_a_fork(monkeypatch) -> None:
    def unexpected_fork_check(*_args):
        raise AssertionError("Le propriétaire ne peut pas forker son propre dépôt.")

    monkeypatch.setattr(contribution, "_fork_exists", unexpected_fork_check)

    assert contribution._ensure_fork(Path("/managed/gh"), "frchalaoux") == (
        "frchalaoux/perfcomparator-results"
    )


def test_submit_public_report_uses_only_github_api_and_opens_a_pull_request(
    tmp_path, monkeypatch
) -> None:
    report = export_public_report(exportable_report())
    public_path = save_public_report(report, tmp_path / "public.json")
    api_calls: list[tuple[str, str, dict[str, object] | None]] = []
    command_calls: list[list[str]] = []

    monkeypatch.setattr(
        contribution,
        "_ensure_fork",
        lambda _gh, _login: "alice/perfcomparator-results",
    )

    def fake_api(_gh, endpoint, *, method="GET", payload=None):
        api_calls.append((endpoint, method, payload))
        if endpoint.endswith("/commits/main"):
            return {"sha": "base-commit", "commit": {"tree": {"sha": "base-tree"}}}
        if endpoint.endswith("/git/blobs"):
            return {"sha": f"blob-{len(api_calls)}"}
        if endpoint.endswith("/git/trees"):
            return {"sha": "new-tree"}
        if endpoint.endswith("/git/commits"):
            return {"sha": "new-commit"}
        if endpoint.endswith("/git/refs"):
            return {"ref": "created"}
        raise AssertionError(endpoint)

    def fake_run(arguments, **_kwargs):
        command_calls.append(arguments)
        return "https://github.com/frchalaoux/perfcomparator-results/pull/42"

    monkeypatch.setattr(contribution, "_api_json", fake_api)
    monkeypatch.setattr(contribution, "_run", fake_run)

    result = contribution.submit_public_report(
        report,
        public_path,
        gh=Path("/managed/gh"),
        login="alice",
    )

    assert result.pull_request_url.endswith("/pull/42")
    assert result.fork == "alice/perfcomparator-results"
    assert result.branch.startswith("add/report-")
    assert all(arguments[0] != "git" for arguments in command_calls)
    tree_payload = next(
        payload for endpoint, _method, payload in api_calls if endpoint.endswith("/git/trees")
    )
    assert tree_payload is not None
    assert [entry["path"] for entry in tree_payload["tree"]] == [
        f"reports/protocol-0.3.0/{report.report_id.removeprefix('sha256:')}.json",
    ]
    ref_payload = next(
        payload for endpoint, _method, payload in api_calls if endpoint.endswith("/git/refs")
    )
    assert ref_payload is not None
    assert str(ref_payload["ref"]).startswith("refs/heads/add/report-")
