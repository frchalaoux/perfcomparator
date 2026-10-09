import hashlib
import io
import zipfile
from pathlib import Path

from perfcomparator import github_cli


def test_managed_github_cli_is_installed_from_a_verified_archive(tmp_path, monkeypatch) -> None:
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, mode="w") as archive:
        archive.writestr("gh_test/bin/gh", b"official-gh-binary")
    archive_bytes = archive_buffer.getvalue()
    digest = hashlib.sha256(archive_bytes).hexdigest()

    monkeypatch.setenv("PERFCOMPARATOR_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(github_cli.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(github_cli.platform, "machine", lambda: "arm64")
    monkeypatch.setitem(
        github_cli.ASSETS,
        ("Darwin", "arm64"),
        ("gh_test.zip", digest),
    )
    monkeypatch.setattr(
        github_cli,
        "_download",
        lambda _url, destination: destination.write_bytes(archive_bytes),
    )

    installed = github_cli.install_managed_github_cli()

    assert installed == tmp_path / "data" / "tools" / "gh"
    assert installed.read_bytes() == b"official-gh-binary"
    assert installed.stat().st_mode & 0o100


def test_github_cli_path_prefers_an_existing_system_installation(monkeypatch) -> None:
    monkeypatch.setattr(github_cli.shutil, "which", lambda _name: "/usr/local/bin/gh")

    assert github_cli.github_cli_path() == Path("/usr/local/bin/gh")
