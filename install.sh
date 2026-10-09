#!/bin/sh
# Installe PerfComparator pour le compte courant (macOS ou Linux).
# Python n'a pas besoin d'être déjà installé : uv gère la version reproductible.
set -eu

release_version="${PERFCOMPARATOR_VERSION:-${BENCHMARK_MAC_VERSION:-v0.5.0}}"
python_version="3.14.4"
script_dir=""
if [ -f "$0" ]; then
    script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || true)
fi

bundled_source_url=""
if [ -n "$script_dir" ] && [ -f "$script_dir/source-url.txt" ]; then
    IFS= read -r bundled_source_url < "$script_dir/source-url.txt"
fi
source_url="${PERFCOMPARATOR_SOURCE:-${BENCHMARK_MAC_SOURCE:-${bundled_source_url:-https://github.com/frchalaoux/perfcomparator/archive/refs/tags/${release_version}.tar.gz}}}"
bundled_web_source_url=""
if [ -n "$script_dir" ] && [ -f "$script_dir/web-source-url.txt" ]; then
    IFS= read -r bundled_web_source_url < "$script_dir/web-source-url.txt"
fi
default_web_source_url="https://github.com/frchalaoux/perfcomparator-web/archive/6bb98c77a8c54b2471bb623e848bfaaf704733b7.tar.gz"
web_source_url="${PERFCOMPARATOR_WEB_SOURCE:-${bundled_web_source_url:-$default_web_source_url}}"
bundled_web_source_version=""
if [ -n "$script_dir" ] && [ -f "$script_dir/web-source-version.txt" ]; then
    IFS= read -r bundled_web_source_version < "$script_dir/web-source-version.txt"
fi
web_source_version="${PERFCOMPARATOR_WEB_VERSION:-${bundled_web_source_version:-0.1.0}}"

if [ -n "$script_dir" ] && [ -f "$script_dir/pyproject.toml" ]; then
    source_url="$script_dir"
fi

if command -v uv >/dev/null 2>&1; then
    uv_command="uv"
elif [ -x "$HOME/.local/bin/uv" ]; then
    uv_command="$HOME/.local/bin/uv"
else
    echo "Installation de uv..."
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        echo "Erreur : curl ou wget est necessaire pour installer uv." >&2
        exit 1
    fi
    uv_command="$HOME/.local/bin/uv"
fi

if [ ! -x "$uv_command" ] && ! command -v "$uv_command" >/dev/null 2>&1; then
    echo "Erreur : uv est introuvable apres son installation." >&2
    exit 1
fi

echo "Installation de CPython ${python_version} gere par uv..."
if ! "$uv_command" python install "$python_version"; then
    echo "La version actuelle de uv ne trouve pas CPython ${python_version}."
    echo "Mise a niveau de uv depuis l'installateur officiel, puis nouvelle tentative..."
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        echo "Erreur : curl ou wget est necessaire pour mettre uv a niveau." >&2
        exit 1
    fi
    uv_command="$HOME/.local/bin/uv"
    if [ ! -x "$uv_command" ]; then
        echo "Erreur : la version mise a niveau de uv est introuvable." >&2
        exit 1
    fi
    if ! "$uv_command" python install "$python_version"; then
        echo "Erreur : CPython ${python_version} reste indisponible apres la mise a niveau de uv." >&2
        exit 1
    fi
fi
legacy_tool_installed=false
if "$uv_command" tool list 2>/dev/null | grep -q '^benchmark-mac v'; then
    legacy_tool_installed=true
fi
if [ "$legacy_tool_installed" = true ]; then
    echo "Nettoyage de l'ancien enregistrement benchmark-mac..."
    "$uv_command" tool uninstall benchmark-mac
fi
echo "Installation de PerfComparator ${release_version}..."
if [ -n "$web_source_url" ]; then
    "$uv_command" tool install --managed-python --python "$python_version" \
        --with-executables-from "perfcomparatorweb @ $web_source_url" \
        --force --reinstall "$source_url"
else
    "$uv_command" tool install --managed-python --python "$python_version" --force --reinstall "$source_url"
fi
if [ -n "$web_source_version" ]; then
    echo "Version PCWEB installée : ${web_source_version}"
fi

tool_bin_dir=$("$uv_command" tool dir --bin)
perfcomparator_command="${tool_bin_dir}/perfcomparator"
if [ -x "$perfcomparator_command" ] && [ -t 1 ]; then
    case "$(uname -s)" in
        Darwin)
            app_dir="$HOME/Applications/PerfComparator.app"
            app_contents="$app_dir/Contents"
            mkdir -p "$app_contents/MacOS"
            printf '#!/bin/sh\nexec "%s" desktop\n' "$perfcomparator_command" \
                > "$app_contents/MacOS/PerfComparator"
            chmod 755 "$app_contents/MacOS/PerfComparator"
            printf '%s\n' \
                '<?xml version="1.0" encoding="UTF-8"?>' \
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' \
                '<plist version="1.0"><dict>' \
                '<key>CFBundleExecutable</key><string>PerfComparator</string>' \
                '<key>CFBundleIdentifier</key><string>org.perfcomparator.app</string>' \
                '<key>CFBundleName</key><string>PerfComparator</string>' \
                '<key>CFBundlePackageType</key><string>APPL</string>' \
                '</dict></plist>' > "$app_contents/Info.plist"
            printf 'APPL????' > "$app_contents/PkgInfo"
            desktop_dir="$HOME/Desktop"
            if [ -d "$desktop_dir" ] && [ ! -e "$desktop_dir/PerfComparator.app" ] && [ ! -L "$desktop_dir/PerfComparator.app" ]; then
                ln -s "$app_dir" "$desktop_dir/PerfComparator.app"
            fi
            echo "Création du lanceur : $app_dir"
            ;;
        Linux)
            launcher="$HOME/.local/bin/perfcomparator-desktop"
            applications_dir="$HOME/.local/share/applications"
            desktop_dir="$HOME/Desktop"
            if command -v xdg-user-dir >/dev/null 2>&1; then
                desktop_dir=$(xdg-user-dir DESKTOP 2>/dev/null || printf '%s' "$desktop_dir")
            fi
            mkdir -p "$(dirname "$launcher")" "$applications_dir"
            printf '#!/bin/sh\nexec "%s" desktop\n' "$perfcomparator_command" > "$launcher"
            chmod 755 "$launcher"
            escaped_launcher=$(printf '%s' "$launcher" | sed 's/\\/\\\\/g; s/"/\\"/g')
            desktop_file="$applications_dir/perfcomparator.desktop"
            printf '%s\n' \
                '[Desktop Entry]' \
                'Type=Application' \
                'Name=PerfComparator' \
                'Comment=Lancer une campagne de benchmarks' \
                'Categories=Science;Utility;' \
                'Terminal=false' \
                "Exec=\"$escaped_launcher\"" \
                'Icon=applications-science' > "$desktop_file"
            chmod 644 "$desktop_file"
            desktop_shortcut="$desktop_dir/PerfComparator.desktop"
            if [ -d "$desktop_dir" ] && [ ! -e "$desktop_shortcut" ] && [ ! -L "$desktop_shortcut" ]; then
                ln -s "$desktop_file" "$desktop_shortcut"
            fi
            echo "Création du lanceur : $desktop_file"
            ;;
    esac
else
    echo
    if command -v perfcomparator >/dev/null 2>&1; then
        echo "PerfComparator est installé. Lancez : perfcomparator web"
    else
        echo "PerfComparator est installé. Fermez et rouvrez le terminal, puis lancez : perfcomparator web"
    fi
fi

if [ -x "$perfcomparator_command" ]; then
    echo "Pour configurer une contribution GitHub : perfcomparator setup-contribution"
fi
