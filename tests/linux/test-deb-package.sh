#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
release_tag=${1:-v0.5.0.dev0}
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT HUP INT TERM

output_dir="$test_dir/dist"
bash "$repo_root/packaging/linux/build-deb.sh" "$release_tag" "$output_dir"

deb_file="$output_dir/PerfComparator-Ubuntu-Debian-amd64.deb"
package_root="$test_dir/extracted"
mkdir -p "$package_root"
dpkg-deb --extract "$deb_file" "$package_root"

expected_version=${release_tag#v}
case "$expected_version" in
    *.dev*) expected_version=$(printf '%s' "$expected_version" | sed 's/\.dev/~dev/') ;;
esac
[ "$(dpkg-deb --field "$deb_file" Package)" = perfcomparator-installer ]
[ "$(dpkg-deb --field "$deb_file" Version)" = "$expected_version" ]
[ "$(dpkg-deb --field "$deb_file" Architecture)" = amd64 ]
[ -x "$package_root/usr/bin/perfcomparator-install" ]
[ -x "$package_root/usr/lib/perfcomparator-installer/install-linux.sh" ]
[ -x "$package_root/usr/lib/perfcomparator-installer/install.sh" ]
[ -f "$package_root/usr/share/applications/perfcomparator-installer.desktop" ]
[ "$(cat "$package_root/usr/lib/perfcomparator-installer/release-version.txt")" = "$release_tag" ]

sh -n "$package_root/usr/bin/perfcomparator-install"
sh -n "$package_root/usr/lib/perfcomparator-installer/install-linux.sh"
sh -n "$package_root/usr/lib/perfcomparator-installer/install.sh"
echo "Debian package smoke test passed for $release_tag"
