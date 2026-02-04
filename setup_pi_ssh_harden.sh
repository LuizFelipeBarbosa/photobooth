#!/usr/bin/env bash
set -euo pipefail

# Disable password SSH auth after key-based auth is installed.
# Run this ON the Pi as root: sudo ./setup_pi_ssh_harden.sh

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (sudo ./setup_pi_ssh_harden.sh)"
  exit 1
fi

CONF="/etc/ssh/sshd_config.d/99-photobooth.conf"
cat > "${CONF}" <<'EOF'
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
EOF

systemctl restart ssh
echo "SSH password authentication disabled. Key auth remains enabled."
