"""Installation locale et contrôlée de GitHub CLI pour les contributions."""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

GITHUB_CLI_VERSION = "2.101.0"
MAX_ARCHIVE_BYTES = 100 * 1_048_576
ASSETS = {
    ("Linux", "x86_64"): (
        "gh_2.101.0_linux_amd64.tar.gz",
        "9bca2d1c16825f109907a23307628a2f0698fbf99662b73a5cf0b020293072b8",
    ),
    ("Linux", "aarch64"): (
        "gh_2.101.0_linux_arm64.tar.gz",
        "b57e8063f18862647c9d22727c32e9da1b963f8bf9db648fe123a6975695640f",
    ),
    ("Darwin", "x86_64"): (
        "gh_2.101.0_macOS_amd64.zip",
        "a6fd66c88e2f07d6e4e058173db341d07dd74d58cf8f19ae668293d2bb614ca3",
    ),
    ("Darwin", "arm64"): (
        "gh_2.101.0_macOS_arm64.zip",
        "e4303e39d8f07141c4bad4b99b01079f05029c59b27076e8fbc825c985ecdd8b",
    ),
    ("Windows", "AMD64"): (
        "gh_2.101.0_windows_amd64.zip",
        "bc6c814367b193cd8e713611d61e36013c0ef843b8f516458fe3eda039192794",
    ),
    ("Windows", "ARM64"): (
        "gh_2.101.0_windows_arm64.zip",
        "e6cbb2d4afdad3e70f3d38b8d1ebaa3a0870a897cfc0e4cf569826710b96b4fd",
    ),
}


def _data_directory() -> Path:
    override = os.environ.get("PERFCOMPARATOR_DATA_DIR")
    if override:
        return Path(override)
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "PerfComparator"
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "perfcomparator"
    return Path.home() / ".local" / "share" / "perfcomparator"


def managed_github_cli_path() -> Path:
    suffix = ".exe" if platform.system() == "Windows" else ""
    return _data_directory() / "tools" / f"gh{suffix}"


def github_cli_path() -> Path | None:
    system_path = shutil.which("gh")
    if system_path:
        return Path(system_path)
    managed = managed_github_cli_path()
    return managed if managed.is_file() else None


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "PerfComparator"})
    total = 0
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("L'archive GitHub CLI dépasse la taille maximale autorisée.")
            output.write(chunk)


def _archive_binary(archive: Path, asset_name: str) -> bytes:
    expected_name = "gh.exe" if "windows" in asset_name else "gh"
    if asset_name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            matches = [name for name in bundle.namelist() if Path(name).name == expected_name]
            if len(matches) != 1:
                raise ValueError("L'exécutable gh est introuvable dans l'archive officielle.")
            return bundle.read(matches[0])
    with tarfile.open(archive, mode="r:gz") as bundle:
        matches = [
            member for member in bundle.getmembers() if Path(member.name).name == expected_name
        ]
        if len(matches) != 1 or not matches[0].isfile():
            raise ValueError("L'exécutable gh est introuvable dans l'archive officielle.")
        extracted = bundle.extractfile(matches[0])
        if extracted is None:
            raise ValueError("L'exécutable gh ne peut pas être lu depuis l'archive officielle.")
        return extracted.read()


def install_managed_github_cli() -> Path:
    """Télécharge l'archive officielle épinglée, la vérifie et installe seulement `gh`."""
    key = (platform.system(), platform.machine())
    try:
        asset_name, expected_digest = ASSETS[key]
    except KeyError as error:
        raise ValueError(
            f"GitHub CLI n'est pas préconfiguré pour {key[0]} {key[1]}. "
            "Consultez https://cli.github.com/."
        ) from error
    url = f"https://github.com/cli/cli/releases/download/v{GITHUB_CLI_VERSION}/{asset_name}"
    destination = managed_github_cli_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perfcomparator-gh-") as temporary_directory:
        archive = Path(temporary_directory) / asset_name
        _download(url, archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != expected_digest:
            raise ValueError("La somme SHA-256 de l'archive GitHub CLI est incorrecte.")
        binary = _archive_binary(archive, asset_name)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(binary)
        temporary.chmod(temporary.stat().st_mode | stat.S_IXUSR)
        temporary.replace(destination)
    return destination
