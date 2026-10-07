#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
release_tag=${1:-v0.5.0}
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT HUP INT TERM

output_dir="$test_dir/dist"
test_pcweb_commit=0123456789abcdef0123456789abcdef01234567
test_pcweb_version=0.1.0
PERFCOMPARATOR_WEB_COMMIT="$test_pcweb_commit" PERFCOMPARATOR_WEB_VERSION="$test_pcweb_version" \
    bash "$repo_root/packaging/linux/build-deb.sh" "$release_tag" "$output_dir"

deb_file="$output_dir/PerfComparator-Ubuntu-Debian-amd64.deb"
package_root="$test_dir/extracted"
mkdir -p "$package_root"
dpkg-deb --extract "$deb_file" "$package_root"

expected_version=${release_tag#v}
case "$expected_version" in
    *.dev*) expected_version=$(printf '%s' "$expected_version" | sed 's/\.dev/~dev/') ;;
esac
expected_source_commit=$(git -C "$repo_root" rev-parse HEAD)
[ "$(dpkg-deb --field "$deb_file" Package)" = perfcomparator-installer ]
[ "$(dpkg-deb --field "$deb_file" Version)" = "$expected_version" ]
[ "$(dpkg-deb --field "$deb_file" Architecture)" = amd64 ]
[ -x "$package_root/usr/bin/perfcomparator-install" ]
[ -x "$package_root/usr/bin/perfcomparator-uninstall" ]
[ -x "$package_root/usr/lib/perfcomparator-installer/install-linux.sh" ]
[ -x "$package_root/usr/lib/perfcomparator-installer/install.sh" ]
[ -x "$package_root/usr/lib/perfcomparator-installer/uninstall.sh" ]
[ -f "$package_root/usr/share/applications/perfcomparator-installer.desktop" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/release-version.txt")" = "$release_tag" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/source-commit.txt")" = "$expected_source_commit" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/source-url.txt")" = \
    "https://github.com/frchalaoux/perfcomparator/archive/$expected_source_commit.tar.gz" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/web-source-commit.txt")" = \
    "$test_pcweb_commit" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/web-source-version.txt")" = \
    "$test_pcweb_version" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/web-source-url.txt")" = \
    "https://github.com/frchalaoux/perfcomparator-web/archive/$test_pcweb_commit.tar.gz" ]

sh -n "$package_root/usr/bin/perfcomparator-install"
sh -n "$package_root/usr/bin/perfcomparator-uninstall"
sh -n "$package_root/usr/lib/perfcomparator-installer/install-linux.sh"
sh -n "$package_root/usr/lib/perfcomparator-installer/install.sh"
sh -n "$package_root/usr/lib/perfcomparator-installer/uninstall.sh"
echo "Debian package smoke test passed for $release_tag"
