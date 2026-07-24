#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/sde}"
MOUNT_POINT="/run/media/chuckles/floppy"
LAUNCH_SCRIPT_NAME="launch.sh"
LOG_TAG="floppy-launcher"
DISPLAY_USER="chuckles"
USER_HOME="/home/chuckles"

log()  { logger -t "$LOG_TAG" -- "$*"; echo "[INFO]  $*"; }
warn() { logger -t "$LOG_TAG" -- "WARN: $*"; echo "[WARN]  $*" >&2; }
die()  { logger -t "$LOG_TAG" -- "ERROR: $*"; echo "[ERROR] $*" >&2; exit 1; }

[[ -b "$DEVICE" ]] || die "Device '$DEVICE' not found."
log "Floppy disk detected on $DEVICE"

mkdir -p "$MOUNT_POINT"

if mountpoint -q "$MOUNT_POINT"; then
    umount "$MOUNT_POINT" || warn "Unmount failed, continuing."
fi

mount -t vfat -o ro,noexec,nosuid,nodev "$DEVICE" "$MOUNT_POINT" \
    || die "Failed to mount $DEVICE."

LAUNCH_FILE="$MOUNT_POINT/$LAUNCH_SCRIPT_NAME"
[[ -f "$LAUNCH_FILE" ]] || { umount "$MOUNT_POINT"; die "No launch.sh found on disk."; }

LAUNCH_CMD="$(grep -v '^\s*#' "$LAUNCH_FILE" | grep -v '^\s*$' | head -1)"
[[ -z "$LAUNCH_CMD" ]] && { umount "$MOUNT_POINT"; die "launch.sh is empty."; }

log "Launch command: $LAUNCH_CMD"

if [[ ! "$LAUNCH_CMD" =~ ^steam:// ]] && \
   [[ ! "$LAUNCH_CMD" =~ ^/usr/bin/steam ]] && \
   [[ ! "$LAUNCH_CMD" =~ ^flatpak\ run\ com\.valvesoftware\.Steam ]]; then
    umount "$MOUNT_POINT"
    die "Rejected: command does not match allowed patterns."
fi

COMPOSITOR_PID="$(pgrep -u "$DISPLAY_USER" -x 'niri|sway|hyprland|kwin_wayland|mutter' | head -1)"
DBUS_SESSION=""
if [[ -n "$COMPOSITOR_PID" ]]; then
    DBUS_SESSION="$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/"$COMPOSITOR_PID"/environ \
        2>/dev/null | tr -d '\0' || true)"
fi

log "Launching as $DISPLAY_USER: $LAUNCH_CMD"

sudo -u "$DISPLAY_USER" env \
    HOME="$USER_HOME" \
    XDG_RUNTIME_DIR="/run/user/$(id -u "$DISPLAY_USER")" \
    WAYLAND_DISPLAY="wayland-1" \
    ${DBUS_SESSION:+$DBUS_SESSION} \
    bash -c "xdg-open '$LAUNCH_CMD'" &

log "Steam launch dispatched (PID $!)."

sleep 3
umount "$MOUNT_POINT" && log "Disk unmounted." || warn "Unmount after launch failed."
