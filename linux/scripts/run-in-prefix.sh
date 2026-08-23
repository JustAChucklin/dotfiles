#!/usr/bin/env bash
#
# run-in-prefix.sh — Run an executable inside a given Steam app's Proton prefix
#
# Usage:
#   ./run-in-prefix.sh <APPID> <path-to-executable.exe> [args...]
#   ./run-in-prefix.sh <APPID> --shell        # drop into a subshell with WINEPREFIX set
#   ./run-in-prefix.sh <APPID> --browse       # just print/open the drive_c path
#
# Example:
#   ./run-in-prefix.sh 1234567890 "/mnt/windrose/tools/SaveTool.exe"

set -euo pipefail

STEAM_ROOT="${STEAM_ROOT:-$HOME/.local/share/Steam}"

# Extra places Proton builds can live besides $STEAM_ROOT/compatibilitytools.d —
# e.g. CachyOS/Arch's steam package ships compat tools system-wide.
EXTRA_COMPAT_DIRS=(
    "/usr/share/steam/compatibilitytools.d"
    "$HOME/.steam/root/compatibilitytools.d"
)

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <APPID> <executable.exe|--shell|--browse> [args...]" >&2
    exit 1
fi

APPID="$1"
shift

COMPATDATA="$STEAM_ROOT/steamapps/compatdata/$APPID"
PREFIX="$COMPATDATA/pfx"

if [[ ! -d "$PREFIX" ]]; then
    echo "Error: no prefix found at $PREFIX" >&2
    echo "Check that APPID '$APPID' is correct and the app has been run at least once." >&2
    exit 1
fi

# --- Handle --browse early: doesn't need Proton at all ---------------------

if [[ "${1:-}" == "--browse" ]]; then
    echo "Prefix C: drive is at:"
    echo "  $PREFIX/drive_c"
    exit 0
fi

# --- Detect which Proton build created this prefix -------------------------

# Respect a manually-set PROTON_DIR (e.g. PROTON_DIR="..." ./run-in-prefix.sh ...)
PROTON_DIR="${PROTON_DIR:-}"

# 1. Steam records the Proton build name in config_info (newer Steam versions).
#    Format varies: sometimes a bare path, sometimes "key=value" style. Scan
#    every line for something that looks like a usable Proton dir.
if [[ -z "$PROTON_DIR" && -f "$COMPATDATA/config_info" ]]; then
    while IFS= read -r LINE; do
        CANDIDATE="${LINE##*=}"
        CANDIDATE="${CANDIDATE%\"}"
        CANDIDATE="${CANDIDATE#\"}"
        if [[ -n "$CANDIDATE" && -x "$CANDIDATE/proton" ]]; then
            PROTON_DIR="$CANDIDATE"
            break
        fi
    done < "$COMPATDATA/config_info"
fi

# 2. Steam also stores which compat tool an app is pinned to in its localconfig.vdf
#    ("CompatToolMapping" -> appid -> name). If we can find that name, resolve it
#    to a directory under common/ or compatibilitytools.d/.
if [[ -z "$PROTON_DIR" ]]; then
    for CFG in "$STEAM_ROOT"/userdata/*/config/localconfig.vdf; do
        [[ -f "$CFG" ]] || continue
        TOOLNAME="$(awk -v appid="\"$APPID\"" '
            $0 ~ appid { found=1 }
            found && /"name"/ { gsub(/[" \t]/,"",$0); split($0,a,"name"); print a[2]; exit }
        ' "$CFG" 2>/dev/null || true)"
        if [[ -n "$TOOLNAME" ]]; then
            for BASE in "$STEAM_ROOT/steamapps/common/$TOOLNAME" "$STEAM_ROOT/compatibilitytools.d/$TOOLNAME" "${EXTRA_COMPAT_DIRS[@]/%//$TOOLNAME}"; do
                if [[ -x "$BASE/proton" ]]; then
                    PROTON_DIR="$BASE"
                    break 2
                fi
            done
        fi
    done
fi

# 3. Fall back: search common + compatibilitytools.d for any proton binary,
#    and let the user pick if there's more than one and we couldn't auto-detect.
if [[ -z "$PROTON_DIR" ]]; then
    mapfile -t CANDIDATES < <(
        find "$STEAM_ROOT/steamapps/common" "$STEAM_ROOT/compatibilitytools.d" \
             "${EXTRA_COMPAT_DIRS[@]}" \
            -maxdepth 1 -type d -iname '*proton*' 2>/dev/null
    )
    if [[ ${#CANDIDATES[@]} -eq 1 ]]; then
        PROTON_DIR="${CANDIDATES[0]}"
    elif [[ ${#CANDIDATES[@]} -gt 1 ]]; then
        echo "Multiple Proton installs found, couldn't auto-detect which one built this prefix:" >&2
        select choice in "${CANDIDATES[@]}"; do
            PROTON_DIR="$choice"
            break
        done
    fi
fi

if [[ -z "$PROTON_DIR" || ! -x "$PROTON_DIR/proton" ]]; then
    echo "Error: could not find a Proton install. Set PROTON_DIR manually and re-run, e.g.:" >&2
    echo "  PROTON_DIR=\"$STEAM_ROOT/steamapps/common/Proton 9.0\" $0 $APPID ..." >&2
    exit 1
fi

export STEAM_COMPAT_DATA_PATH="$COMPATDATA"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_ROOT"

echo "Using Proton: $PROTON_DIR"
echo "Using prefix: $PREFIX"

# --- Modes -------------------------------------------------------------------

MODE="${1:-}"

case "$MODE" in
    --shell)
        echo "Dropping into a subshell with WINEPREFIX set. Type 'exit' to leave."
        WINEPREFIX="$PREFIX" exec "$SHELL"
        ;;
    "")
        echo "Error: no executable, --shell, or --browse specified." >&2
        exit 1
        ;;
    *)
        EXE="$1"
        shift
        if [[ ! -f "$EXE" ]]; then
            echo "Error: executable not found: $EXE" >&2
            exit 1
        fi
        echo "Running: $EXE $*"
        "$PROTON_DIR/proton" run "$EXE" "$@"
        ;;
esac

