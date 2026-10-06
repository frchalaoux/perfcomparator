import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("platform", ["Linux", "Darwin"])
def test_posix_uninstaller_removes_only_product_files(tmp_path: Path, platform: str) -> None:
    home = tmp_path / "home"
    fake_bin = tmp_path / "bin"
    tool_bin = tmp_path / "uv-tool-bin"
    home.mkdir()
    fake_bin.mkdir()
    tool_bin.mkdir()
    tool_log = tmp_path / "uv.log"

    uv = fake_bin / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$UV_LOG"\n'
        'case "$*" in\n'
        '  "tool dir --bin") printf "%s\\n" "$UV_TOOL_BIN" ;;\n'
        '  "tool list") printf "%s\\n" "perfcomparator v0.5.0" ;;\n'
        '  "tool uninstall perfcomparator") ;;\n'
        "  *) exit 2 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    fake_uname = fake_bin / "uname"
    fake_uname.write_text(f"#!/bin/sh\nprintf '%s\\n' '{platform}'\n", encoding="utf-8")
    fake_uname.chmod(0o755)
    fake_xdg = fake_bin / "xdg-user-dir"
    fake_xdg.write_text('#!/bin/sh\nprintf "%s\\n" "$XDG_DESKTOP"\n', encoding="utf-8")
    fake_xdg.chmod(0o755)

    preserved_report = home / "perfcomparator" / "data" / "results" / "report.json"
    preserved_log = home / ".local" / "share" / "PerfComparator" / "logs" / "install.log"
    preserved_report.parent.mkdir(parents=True)
    preserved_log.parent.mkdir(parents=True)
    preserved_report.write_text("report", encoding="utf-8")
    preserved_log.write_text("log", encoding="utf-8")

    if platform == "Linux":
        launcher = home / ".local" / "bin" / "perfcomparator-desktop"
        applications = home / ".local" / "share" / "applications"
        desktop_file = applications / "perfcomparator.desktop"
        desktop_link = home / "Desktop" / "PerfComparator.desktop"
        launcher.parent.mkdir(parents=True)
        applications.mkdir(parents=True)
        desktop_link.parent.mkdir(parents=True)
        launcher.write_text(
            f'#!/bin/sh\nexec "{tool_bin / "perfcomparator"}" desktop\n', encoding="utf-8"
        )
        desktop_file.write_text(
            f'[Desktop Entry]\nType=Application\nName=PerfComparator\nExec="{launcher}"\n',
            encoding="utf-8",
        )
        desktop_link.symlink_to(desktop_file)
        unrelated = home / ".local" / "bin" / "another-tool"
        unrelated.write_text("keep", encoding="utf-8")
    else:
        app = home / "Applications" / "PerfComparator.app"
        app_contents = app / "Contents"
        app_executable = app_contents / "MacOS" / "PerfComparator"
        desktop_link = home / "Desktop" / "PerfComparator.app"
        app_executable.parent.mkdir(parents=True)
        desktop_link.parent.mkdir(parents=True)
        (app_contents / "Info.plist").write_text(
            "<plist><dict><key>CFBundleIdentifier</key>"
            "<string>org.perfcomparator.app</string></dict></plist>",
            encoding="utf-8",
        )
        app_executable.write_text(
            f'#!/bin/sh\nexec "{tool_bin / "perfcomparator"}" desktop\n', encoding="utf-8"
        )
        desktop_link.symlink_to(app)
        unrelated = home / "Applications" / "Other.app"
        unrelated.mkdir()

    environment = os.environ | {
        "HOME": str(home),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "UV_LOG": str(tool_log),
        "UV_TOOL_BIN": str(tool_bin),
        "XDG_DESKTOP": "",
    }
    result = subprocess.run(
        ["sh", str(ROOT / "uninstall.sh"), "--yes"],
        check=True,
        env=environment,
        text=True,
        capture_output=True,
    )

    assert "tool uninstall perfcomparator" in tool_log.read_text(encoding="utf-8")
    assert not desktop_link.is_symlink()
    assert preserved_report.read_text(encoding="utf-8") == "report"
    assert preserved_log.read_text(encoding="utf-8") == "log"
    assert unrelated.exists()
    if platform == "Linux":
        assert not launcher.exists()
        assert not desktop_file.exists()
    else:
        assert not app.exists()
    assert "Python géré par uv" in result.stdout


def test_posix_uninstaller_requires_confirmation_without_tty(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uv = fake_bin / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  "tool dir --bin") printf "%s\\n" "$UV_TOOL_BIN" ;;\n'
        '  "tool list") printf "%s\\n" "perfcomparator v0.5.0" ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    environment = os.environ | {
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "UV_TOOL_BIN": str(tmp_path / "tool-bin"),
    }

    result = subprocess.run(
        ["sh", str(ROOT / "uninstall.sh")],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Confirmation requise" in result.stderr
