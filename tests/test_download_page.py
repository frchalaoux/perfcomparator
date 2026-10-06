from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_download_page_exposes_cross_platform_uninstallers() -> None:
    page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "package-installers.yml").read_text(
        encoding="utf-8"
    )
    promotion = (ROOT / ".github" / "workflows" / "promote-tested-release.yml").read_text(
        encoding="utf-8"
    )
    expected_assets = (
        "PerfComparator-uninstall-macOS.sh",
        "PerfComparator-uninstall-Windows.ps1",
        "PerfComparator-uninstall-Linux.sh",
    )

    for asset_name in expected_assets:
        assert f'data-asset="{asset_name}"' in page
        assert asset_name in workflow
        assert asset_name in promotion

    assert "gh run download" in promotion
    assert "sha256sum --check --strict" in promotion
    assert "gh release create" in promotion

    assert page.count('<a class="download" data-uninstaller ') == len(expected_assets)
    assert page.count("data-fallback-url=") == len(expected_assets)
    assert "data-required='true'" in page
