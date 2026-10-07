"""Soumission guidée d'un rapport public au catalogue communautaire."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .models import PublicBenchmarkReport

CATALOG_REPOSITORY = "frchalaoux/perfcomparator-results"


@dataclass(frozen=True)
class ContributionResult:
    pull_request_url: str
    branch: str
    fork: str


def _run(
    arguments: list[str],
    *,
    capture: bool = True,
    input_text: str | None = None,
) -> str:
    try:
        completed = subprocess.run(
            arguments,
            check=True,
            text=True,
            capture_output=capture,
            input=input_text,
        )
    except FileNotFoundError as error:
        raise ValueError(f"Commande introuvable : {arguments[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "erreur inconnue").strip()
        raise ValueError(f"La commande {arguments[0]} a échoué : {detail}") from error
    return completed.stdout.strip() if capture else ""


def _api_json(
    gh: Path,
    endpoint: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    arguments = [str(gh), "api", "--method", method, endpoint]
    input_text = None
    if payload is not None:
        arguments.extend(["--input", "-"])
        input_text = json.dumps(payload, ensure_ascii=False)
    output = _run(arguments, input_text=input_text)
    parsed = json.loads(output)
    if not isinstance(parsed, dict):
        raise TypeError(f"Réponse GitHub inattendue pour {endpoint}.")
    return parsed


def github_login(gh: Path) -> str:
    """Connecte GitHub CLI si nécessaire et retourne le compte actif."""
    status = subprocess.run(
        [str(gh), "auth", "status", "--hostname", "github.com"],
        check=False,
        text=True,
        capture_output=True,
    )
    if status.returncode != 0:
        _run(
            [
                str(gh),
                "auth",
                "login",
                "--hostname",
                "github.com",
                "--git-protocol",
                "https",
                "--web",
            ],
            capture=False,
        )
    login = str(_api_json(gh, "user")["login"])
    if not login:
        raise ValueError("Le compte GitHub actif est introuvable.")
    return login


def _fork_exists(gh: Path, login: str) -> bool:
    completed = subprocess.run(
        [str(gh), "api", f"repos/{login}/perfcomparator-results"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return False
    payload = json.loads(completed.stdout)
    if not payload.get("fork") or payload.get("parent", {}).get("full_name") != CATALOG_REPOSITORY:
        raise ValueError(
            f"Le dépôt {login}/perfcomparator-results existe mais n'est pas le fork attendu."
        )
    return True


def _ensure_fork(gh: Path, login: str) -> str:
    if login == CATALOG_REPOSITORY.partition("/")[0]:
        return CATALOG_REPOSITORY
    fork = f"{login}/perfcomparator-results"
    if not _fork_exists(gh, login):
        created = _api_json(
            gh,
            f"repos/{CATALOG_REPOSITORY}/forks",
            method="POST",
        )
        if created.get("full_name") != fork:
            raise ValueError(f"Le fork créé est inattendu : {created}")
        for _ in range(20):
            if _fork_exists(gh, login):
                break
            time.sleep(1)
        else:
            raise ValueError("Le fork GitHub n'est pas devenu disponible dans le délai prévu.")
    return fork


def _create_blob(gh: Path, fork: str, content: str) -> str:
    response = _api_json(
        gh,
        f"repos/{fork}/git/blobs",
        method="POST",
        payload={"content": content, "encoding": "utf-8"},
    )
    return str(response["sha"])


def submit_public_report(
    report: PublicBenchmarkReport,
    public_path: Path,
    *,
    gh: Path,
    login: str,
) -> ContributionResult:
    """Crée le fork, une branche par API et ouvre la pull request."""
    fork = _ensure_fork(gh, login)
    digest = report.report_id.removeprefix("sha256:")
    branch = f"add/report-{digest[:12]}-{datetime.now(UTC):%Y%m%d%H%M%S}"
    report_path = f"reports/protocol-{report.protocol_version}/{digest}.json"
    report_content = public_path.read_text(encoding="utf-8")

    base = _api_json(gh, f"repos/{CATALOG_REPOSITORY}/commits/main")
    try:
        base_commit = str(base["sha"])
        base_tree = str(base["commit"]["tree"]["sha"])
    except (KeyError, TypeError) as error:
        raise ValueError("La branche principale du catalogue est illisible.") from error

    report_blob = _create_blob(gh, fork, report_content)
    tree = _api_json(
        gh,
        f"repos/{fork}/git/trees",
        method="POST",
        payload={
            "base_tree": base_tree,
            "tree": [
                {"path": report_path, "mode": "100644", "type": "blob", "sha": report_blob},
            ],
        },
    )
    commit = _api_json(
        gh,
        f"repos/{fork}/git/commits",
        method="POST",
        payload={
            "message": "Add community benchmark report",
            "tree": str(tree["sha"]),
            "parents": [base_commit],
        },
    )
    _api_json(
        gh,
        f"repos/{fork}/git/refs",
        method="POST",
        payload={"ref": f"refs/heads/{branch}", "sha": str(commit["sha"])},
    )

    body = (
        "## Rapport communautaire\n\n"
        f"- identifiant : `{report.report_id}`\n"
        f"- protocole : `{report.protocol_version}`\n"
        f"- profil : `{report.profile}`\n"
        f"- résultats : {len(report.results)}\n\n"
        "Rapport public CC0-1.0, communautaire et non certifié. "
        "Contribution préparée par `perfcomparator contribute`."
    )
    pull_request_url = _run(
        [
            str(gh),
            "pr",
            "create",
            "--repo",
            CATALOG_REPOSITORY,
            "--base",
            "main",
            "--head",
            f"{login}:{branch}",
            "--title",
            "Add community benchmark report",
            "--body",
            body,
        ]
    )
    return ContributionResult(pull_request_url=pull_request_url, branch=branch, fork=fork)
