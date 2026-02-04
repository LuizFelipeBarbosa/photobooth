#!/usr/bin/env bash
set -euo pipefail

# Setup script for Photobooth auto-start on Raspberry Pi.
# Usage:
#   sudo ./setup_pi.sh
#
# Optional overrides:
#   PB_SERVICE_USER=pi
#   PB_APP_DIR=/home/pi/photobooth
#   PB_PYTHON_BIN=/home/pi/photobooth/venv/bin/python
#   PB_START_NOW=true

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (sudo ./setup_pi.sh)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_TEMPLATE="${SCRIPT_DIR}/photobooth.service"
SERVICE_DEST="/etc/systemd/system/photobooth.service"

if [[ ! -f "${SERVICE_TEMPLATE}" ]]; then
  echo "Service template not found: ${SERVICE_TEMPLATE}"
  exit 1
fi

if [[ -n "${PB_SERVICE_USER:-}" ]]; then
  SERVICE_USER="${PB_SERVICE_USER}"
elif [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  SERVICE_USER="${SUDO_USER}"
else
  SERVICE_USER="$(stat -c '%U' "${SCRIPT_DIR}")"
fi

if [[ -z "${SERVICE_USER}" || "${SERVICE_USER}" == "root" ]]; then
  echo "Could not determine a non-root service user."
  echo "Re-run with PB_SERVICE_USER=<your_pi_user> sudo ./setup_pi.sh"
  exit 1
fi

if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
  echo "User does not exist: ${SERVICE_USER}"
  exit 1
fi

APP_DIR="${PB_APP_DIR:-${SCRIPT_DIR}}"
if [[ ! -d "${APP_DIR}" ]]; then
  echo "App directory not found: ${APP_DIR}"
  exit 1
fi

PYTHON_BIN="${PB_PYTHON_BIN:-${APP_DIR}/venv/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
    echo "Warning: venv python not found, using system python: ${PYTHON_BIN}"
  else
    echo "Python executable not found: ${PYTHON_BIN}"
    exit 1
  fi
fi

START_NOW="${PB_START_NOW:-true}"

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\/&|]/\\&/g'
}

SERVICE_USER_ESCAPED="$(escape_sed_replacement "${SERVICE_USER}")"
APP_DIR_ESCAPED="$(escape_sed_replacement "${APP_DIR}")"
PYTHON_BIN_ESCAPED="$(escape_sed_replacement "${PYTHON_BIN}")"

TMP_SERVICE="$(mktemp)"
trap 'rm -f "${TMP_SERVICE}"' EXIT

sed \
  -e "s|{{PHOTOBOOTH_USER}}|${SERVICE_USER_ESCAPED}|g" \
  -e "s|{{PHOTOBOOTH_DIR}}|${APP_DIR_ESCAPED}|g" \
  -e "s|{{PHOTOBOOTH_PYTHON}}|${PYTHON_BIN_ESCAPED}|g" \
  "${SERVICE_TEMPLATE}" > "${TMP_SERVICE}"

echo "Installing systemd service..."
cp "${TMP_SERVICE}" "${SERVICE_DEST}"

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling service on boot..."
systemctl enable photobooth.service

if [[ "${START_NOW}" == "true" ]]; then
  if systemctl is-active --quiet photobooth.service; then
    echo "Restarting photobooth service..."
    systemctl restart photobooth.service
  else
    echo "Starting photobooth service..."
    systemctl start photobooth.service
  fi
  systemctl status photobooth.service --no-pager
else
  echo "Service enabled but not started (PB_START_NOW=${START_NOW})."
fi

echo "Setup complete."
echo "Service user: ${SERVICE_USER}"
echo "App directory: ${APP_DIR}"
echo "Python bin: ${PYTHON_BIN}"
