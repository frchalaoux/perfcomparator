import os
import subprocess
import tomllib
from pathlib import Path

from benchmark_mac import __version__

ROOT = Path(__file__).parents[1]
PUBLISHED_VERSION = "0.4.0"
EXPECTED_TAG = f"v{PUBLISHED_VERSION}"
CANDIDATE_TAG = "v0.5.0.dev0"


def test_versions_are_consistent_across_package_and_installers() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    posix_installer = (ROOT / "install.sh").read_text(encoding="utf-8")
    windows_installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    versions = (ROOT / "docs" / "versions.md").read_text(encoding="utf-8")

    assert project["project"]["name"] == "perfcomparator"
    assert project["project"]["version"] == __version__
    assert project["project"]["urls"]["Repository"] == (
        "https://github.com/frchalaoux/perfcomparator.git"
    )
    assert project["project"]["scripts"] == {
        "perfcomparator": "benchmark_mac.cli:app",
        "benchmark-mac": "benchmark_mac.cli:app",
    }
    assert CANDIDATE_TAG in posix_installer
    assert CANDIDATE_TAG in windows_installer
    assert CANDIDATE_TAG in readme
    assert CANDIDATE_TAG in versions
    assert "PERFCOMPARATOR_VERSION" in posix_installer
    assert "PERFCOMPARATOR_VERSION" in windows_installer
    assert "BENCHMARK_MAC_VERSION" in posix_installer
    assert "BENCHMARK_MAC_VERSION" in windows_installer
    assert "tool uninstall benchmark-mac" in posix_installer
    assert 'ArgumentList @("tool", "uninstall", "benchmark-mac")' in windows_installer
    assert "setup-contribution --yes" not in posix_installer
    assert "setup-contribution --yes" not in windows_installer
    assert "perfcomparator setup-contribution" in posix_installer
    assert "perfcomparator setup-contribution" in windows_installer
    assert "Start-Process" not in windows_installer
    assert "open \"$app_dir\"" not in posix_installer
    assert '\n            "$launcher"\n' not in posix_installer
    windows_batch = (ROOT / "install.bat").read_text(encoding="utf-8")
    assert "where pwsh.exe" in windows_batch
    assert "pwsh.exe -NoProfile" in windows_batch
    assert "powershell.exe -NoProfile" in windows_batch
    assert windows_batch.index("pwsh.exe -NoProfile") < windows_batch.index(
        "powershell.exe -NoProfile"
    )
    assert "Compatible avec Windows PowerShell 5.1 et PowerShell 7." in windows_installer
    assert "Install-CurrentUv" in windows_installer
    assert '"-File", $installerPath' in windows_installer
    assert "irm https://astral.sh/uv/install.ps1 | iex" not in windows_installer
    assert "Graphical shortcut not created; CLI remains available." in windows_installer
    expected_posix_url = (
        f"https://raw.githubusercontent.com/frchalaoux/perfcomparator/{EXPECTED_TAG}/install.sh"
    )
    expected_windows_url = (
        f"https://raw.githubusercontent.com/frchalaoux/perfcomparator/{EXPECTED_TAG}/install.ps1"
    )
    for document in (readme, versions):
        assert PUBLISHED_VERSION in document
        assert expected_posix_url in document
        assert expected_windows_url in document
    assert "/v0.3.0.dev0/install.sh" in versions
    assert "/v0.3.0.dev0/install.ps1" in versions


def test_release_archives_include_platform_uninstallers() -> None:
    workflow = (ROOT / ".github" / "workflows" / "package-installers.yml").read_text(
        encoding="utf-8"
    )

    assert "cp install.command install.sh uninstall.sh" in workflow
    assert "Copy-Item install.bat, install.ps1, uninstall.ps1" in workflow
    assert "cp install.desktop install-linux.sh install.sh uninstall.sh" in workflow


def test_posix_installer_defaults_to_its_own_tag(tmp_path: Path) -> None:
    installer = tmp_path / "install.sh"
    installer.write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv = fake_bin / "uv"
    uv.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$UV_LOG"\n', encoding="utf-8")
    uv.chmod(0o755)
    log = tmp_path / "uv.log"
    environment = os.environ | {
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "UV_LOG": str(log),
    }
    environment.pop("BENCHMARK_MAC_SOURCE", None)
    environment.pop("BENCHMARK_MAC_VERSION", None)
    environment.pop("PERFCOMPARATOR_SOURCE", None)
    environment.pop("PERFCOMPARATOR_VERSION", None)

    subprocess.run(["sh", str(installer)], check=True, env=environment, capture_output=True)

    calls = log.read_text(encoding="utf-8")
    assert f"archive/refs/tags/{CANDIDATE_TAG}.tar.gz" in calls
    assert "refs/tags/v0.1.0.tar.gz" not in calls


def test_posix_installer_honors_an_explicit_source(tmp_path: Path) -> None:
    installer = tmp_path / "install.sh"
    installer.write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv = fake_bin / "uv"
    uv.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$UV_LOG"\n', encoding="utf-8")
    uv.chmod(0o755)
    log = tmp_path / "uv.log"
    source = "https://example.invalid/perfcomparator.tar.gz"
    environment = os.environ | {
        "PERFCOMPARATOR_SOURCE": source,
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "UV_LOG": str(log),
    }

    subprocess.run(["sh", str(installer)], check=True, env=environment, capture_output=True)

    assert source in log.read_text(encoding="utf-8")


def test_posix_installer_leaves_contribution_setup_to_the_user(tmp_path: Path) -> None:
    installer = tmp_path / "install.sh"
    installer.write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv = fake_bin / "uv"
    uv.write_text(
        '#!/bin/sh\ncase "$*" in "tool dir --bin") printf "%s\\n" "$FAKE_TOOL_BIN";; esac\n',
        encoding="utf-8",
    )
    uv.chmod(0o755)
    tool_bin = tmp_path / "tool-bin"
    tool_bin.mkdir()
    perfcomparator = tool_bin / "perfcomparator"
    perfcomparator.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> "$CONTRIBUTION_LOG"\n',
        encoding="utf-8",
    )
    perfcomparator.chmod(0o755)
    log = tmp_path / "contribution.log"
    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "FAKE_TOOL_BIN": str(tool_bin),
        "CONTRIBUTION_LOG": str(log),
    }

    subprocess.run(["sh", str(installer)], check=True, env=environment, capture_output=True)

    assert not log.exists()


def test_posix_installer_cleans_up_the_legacy_tool_after_installing(tmp_path: Path) -> None:
    installer = tmp_path / "install.sh"
    installer.write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv = fake_bin / "uv"
    uv.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> "$UV_LOG"\n'
        'case "$*" in "tool list") printf "%s\\n" "benchmark-mac v0.3.2";; esac\n',
        encoding="utf-8",
    )
    uv.chmod(0o755)
    log = tmp_path / "uv.log"
    environment = os.environ | {
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "UV_LOG": str(log),
    }

    subprocess.run(["sh", str(installer)], check=True, env=environment, capture_output=True)

    calls = log.read_text(encoding="utf-8")
    assert calls.count("tool install --managed-python") == 1
    assert "tool uninstall benchmark-mac" in calls
    assert calls.index("tool uninstall benchmark-mac") < calls.index(
        "tool install --managed-python"
    )


def test_posix_installer_updates_uv_and_retries_when_python_is_unknown(tmp_path: Path) -> None:
    installer = tmp_path / "install.sh"
    installer.write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    managed_bin = tmp_path / ".local" / "bin"
    managed_bin.mkdir(parents=True)
    old_uv = fake_bin / "uv"
    old_uv.write_text(
        '#!/bin/sh\nprintf "%s\\n" "old:$*" >> "$UV_LOG"\n'
        'case "$*" in "python install "*) exit 2;; esac\n',
        encoding="utf-8",
    )
    old_uv.chmod(0o755)
    updated_uv = tmp_path / "updated-uv"
    updated_uv.write_text(
        '#!/bin/sh\nprintf "%s\\n" "updated:$*" >> "$UV_LOG"\n',
        encoding="utf-8",
    )
    updated_uv.chmod(0o755)
    curl = fake_bin / "curl"
    curl.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' "
        '\'cp "$FAKE_UPDATED_UV" "$HOME/.local/bin/uv"\' '
        "'chmod +x \"$HOME/.local/bin/uv\"'\n",
        encoding="utf-8",
    )
    curl.chmod(0o755)
    log = tmp_path / "uv.log"
    environment = os.environ | {
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "FAKE_UPDATED_UV": str(updated_uv),
        "UV_LOG": str(log),
    }

    subprocess.run(["sh", str(installer)], check=True, env=environment, capture_output=True)

    calls = log.read_text(encoding="utf-8")
    assert "old:python install 3.14.4" in calls
    assert "updated:python install 3.14.4" in calls
    assert "updated:tool install" in calls
