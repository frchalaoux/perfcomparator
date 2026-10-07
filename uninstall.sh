#!/bin/sh
# Désinstalle PerfComparator pour le compte courant (macOS ou Linux).
set -eu

assume_yes=false
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--yes" ]; }; then
    echo "Usage : $0 [--yes]" >&2
    exit 2
fi
if [ "$#" -eq 1 ]; then
    assume_yes=true
fi

case "$(uname -s)" in
    Darwin|Linux) platform=$(uname -s) ;;
    *) echo "Ce désinstallateur prend en charge macOS et Linux." >&2; exit 1 ;;
esac
if [ -z "${HOME:-}" ]; then
    echo "Le répertoire personnel du compte est introuvable ; aucune modification n'a été effectuée." >&2
    exit 1
fi

if command -v uv >/dev/null 2>&1; then
    uv_command=$(command -v uv)
elif [ -x "$HOME/.local/bin/uv" ]; then
    uv_command="$HOME/.local/bin/uv"
else
    echo "uv est introuvable ; aucune modification n'a été effectuée." >&2
    exit 1
fi

tool_bin_dir=$("$uv_command" tool dir --bin)
tool_list=$("$uv_command" tool list)

if [ "$assume_yes" != true ]; then
    if [ ! -t 0 ]; then
        echo "Confirmation requise. Relancez avec --yes pour confirmer." >&2
        exit 2
    fi
    printf "Désinstaller PerfComparator pour l'utilisateur %s ? [o/N] " "$(id -un)"
    IFS= read -r answer || answer=""
    case "$answer" in
        o|O|oui|Oui|OUI|y|Y|yes|Yes|YES) ;;
        *) echo "Désinstallation annulée."; exit 0 ;;
    esac
fi

perfcomparator_command="$tool_bin_dir/perfcomparator"
perfcomparatorweb_command="$tool_bin_dir/perfcomparatorweb"
if [ -x "$perfcomparator_command" ] && [ -x "$perfcomparatorweb_command" ]; then
    echo "Arrêt de PCWEB et PCE avant la désinstallation..."
    "$perfcomparator_command" web stop
fi

if printf '%s\n' "$tool_list" | grep -Eq '^perfcomparator v'; then
    echo "Désinstallation de PerfComparator..."
    "$uv_command" tool uninstall perfcomparator
else
    echo "PerfComparator n'est pas enregistré comme outil uv ; nettoyage des lanceurs uniquement."
fi

if [ "$platform" = Darwin ]; then
    app_dir="$HOME/Applications/PerfComparator.app"
    app_contents="$app_dir/Contents"
    desktop_link="$HOME/Desktop/PerfComparator.app"
    executable="$app_contents/MacOS/PerfComparator"

    if [ -L "$desktop_link" ] && [ "$(readlink "$desktop_link")" = "$app_dir" ]; then
        rm -f "$desktop_link"
        echo "Raccourci supprimé : $desktop_link"
    fi

    if [ -d "$app_dir" ]; then
        if [ -f "$app_contents/Info.plist" ] &&
            grep -Fq '<string>org.perfcomparator.app</string>' "$app_contents/Info.plist" &&
            [ -f "$executable" ] &&
            grep -Fq "exec \"$tool_bin_dir/perfcomparator\" desktop" "$executable"; then
            rm -rf "$app_dir"
            echo "Application supprimée : $app_dir"
        else
            echo "Bundle non reconnu, conservé : $app_dir" >&2
        fi
    fi
else
    launcher="$HOME/.local/bin/perfcomparator-desktop"
    applications_dir="$HOME/.local/share/applications"
    desktop_file="$applications_dir/perfcomparator.desktop"
    desktop_dir="$HOME/Desktop"
    if command -v xdg-user-dir >/dev/null 2>&1; then
        configured_desktop_dir=$(xdg-user-dir DESKTOP 2>/dev/null || true)
        if [ -n "$configured_desktop_dir" ]; then
            desktop_dir=$configured_desktop_dir
        fi
    fi
    desktop_link="$desktop_dir/PerfComparator.desktop"

    if [ -L "$desktop_link" ] && [ "$(readlink "$desktop_link")" = "$desktop_file" ]; then
        rm -f "$desktop_link"
        echo "Raccourci supprimé : $desktop_link"
    fi

    if [ -f "$launcher" ] &&
        grep -Fqx '#!/bin/sh' "$launcher" &&
        grep -Fqx "exec \"$tool_bin_dir/perfcomparator\" desktop" "$launcher"; then
        rm -f "$launcher"
        echo "Lanceur supprimé : $launcher"
    fi

    if [ -f "$desktop_file" ] &&
        grep -Fqx 'Name=PerfComparator' "$desktop_file" &&
        grep -Fqx "Exec=\"$launcher\"" "$desktop_file"; then
        rm -f "$desktop_file"
        echo "Entrée de menu supprimée : $desktop_file"
    fi
fi

echo "PerfComparator est désinstallé."
echo "uv, Python géré par uv, rapports et journaux ont été conservés."
