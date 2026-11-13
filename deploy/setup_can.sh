#!/usr/bin/env bash
# Bring up SocketCAN on the Linux host. Requires root; never called by bootstrap.
# Bitrate MUST be verified against the AgileX PiPER / CAN adapter manual.
set -euo pipefail

IFACE="${PASD_CAN_INTERFACE:-can0}"
BITRATE="${PASD_CAN_BITRATE:-1000000}"
DRY_RUN="${PASD_CAN_DRY_RUN:-0}"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run with sudo, e.g. sudo PASD_CAN_INTERFACE=can0 ./deploy/setup_can.sh" >&2
  exit 1
fi

if ! command -v ip >/dev/null 2>&1; then
  echo "ERROR: iproute2 not installed (apt install iproute2)" >&2
  exit 1
fi

echo "[can] interface=$IFACE bitrate=$BITRATE (verify against the hardware manual)"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[can] dry-run: no changes made"
  exit 0
fi

for module in can can_raw; do
  modprobe "$module" 2>/dev/null || echo "[can] note: module $module not loaded (container?)"
done

if ! ip link show "$IFACE" >/dev/null 2>&1; then
  echo "ERROR: interface $IFACE not found. Check the adapter, driver and udev rule." >&2
  echo "       ip -details link show" >&2
  exit 1
fi

ip link set "$IFACE" down 2>/dev/null || true
ip link set "$IFACE" up type can bitrate "$BITRATE"
echo "[can] up:"
ip -details link show "$IFACE" | sed -n '1,6p'
