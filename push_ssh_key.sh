#!/usr/bin/env bash
set -euo pipefail

# Push your local public key to the Pi's authorized_keys.
# Run this from your Mac:
#   ./push_ssh_key.sh [user@host] [path_to_pubkey]
#
# Defaults:
#   user@host: pi2@10.0.0.71
#   pubkey:    ~/.ssh/id_ed25519.pub

USER_HOST="${1:-pi2@10.0.0.71}"
PUBKEY="${2:-$HOME/.ssh/id_ed25519.pub}"

if [[ ! -f "${PUBKEY}" ]]; then
  echo "Public key not found: ${PUBKEY}"
  echo "Generate one with: ssh-keygen -t ed25519 -C \"photobooth-admin\""
  exit 1
fi

ssh "${USER_HOST}" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
cat "${PUBKEY}" | ssh "${USER_HOST}" "cat >> ~/.ssh/authorized_keys"

echo "Key appended to ${USER_HOST}:~/.ssh/authorized_keys"
