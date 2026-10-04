#!/bin/sh
# Build the Ubuntu/Debian bootstrap package for a tagged source release.
set -eu

release_tag=${1:?Usage: build-deb.sh RELEASE_TAG [OUTPUT_DIR]}
output_dir=${2:-dist}
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

if ! printf '%s\n' "$release_tag" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+(\.dev[0-9]+)?$'; then
    echo "Error: expected a release tag like v1.2.3 or v1.2.3.dev0." >&2
    exit 1
fi
if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "Error: dpkg-deb is required to build the Debian package." >&2
    exit 1
fi
if [ ! -f "$repo_root/install-linux.sh" ] || [ ! -f "$repo_root/install.sh" ]; then
    echo "Error: run this builder from a PerfComparator source tree." >&2
    exit 1
fi

version=${release_tag#v}
case "$version" in
    *.dev*) debian_version=$(printf '%s' "$version" | sed 's/\.dev/~dev/') ;;
    *) debian_version=$version ;;
esac

case "$output_dir" in
    /*) ;;
    *) output_dir="$PWD/$output_dir" ;;
esac
mkdir -p "$output_dir"

work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT HUP INT TERM
package_root="$work_dir/package"
mkdir -p \
    "$package_root/DEBIAN" \
    "$package_root/usr/bin" \
    "$package_root/usr/lib/perfcomparator-installer" \
    "$package_root/usr/share/applications"

sed "s/@VERSION@/$debian_version/" \
    "$repo_root/packaging/linux/deb/control.in" \
    > "$package_root/DEBIAN/control"
cp "$repo_root/packaging/linux/deb/perfcomparator-installer.desktop" \
    "$package_root/usr/share/applications/perfcomparator-installer.desktop"
cp "$repo_root/packaging/linux/deb/perfcomparator-install" \
    "$package_root/usr/bin/perfcomparator-install"
cp "$repo_root/install-linux.sh" "$repo_root/install.sh" \
    "$package_root/usr/lib/perfcomparator-installer/"
printf '%s\n' "$release_tag" \
    > "$package_root/usr/lib/perfcomparator-installer/release-version.txt"
chmod 755 \
    "$package_root/usr/bin/perfcomparator-install" \
    "$package_root/usr/lib/perfcomparator-installer/install-linux.sh" \
    "$package_root/usr/lib/perfcomparator-installer/install.sh"
chmod 644 \
    "$package_root/DEBIAN/control" \
    "$package_root/usr/share/applications/perfcomparator-installer.desktop" \
    "$package_root/usr/lib/perfcomparator-installer/release-version.txt"

dpkg-deb --root-owner-group --build \
    "$package_root" \
    "$output_dir/PerfComparator-Ubuntu-Debian-amd64.deb"
