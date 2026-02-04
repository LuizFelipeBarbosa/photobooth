#!/usr/bin/env bash
set -euo pipefail

# Configure Raspberry Pi as a Wi-Fi hotspot with a captive portal that
# redirects all HTTP traffic to the photobooth app (default: :8080).
# This script is intentionally on-demand: it does not enable hotspot
# services at boot, so it must be run manually after each reboot.
#
# Usage:
#   sudo ./setup_pi_hotspot.sh
#
# Optional overrides:
#   HOTSPOT_IFACE=wlan0
#   HOTSPOT_SSID=Photobooth
#   HOTSPOT_PSK=change-me-now
#   HOTSPOT_COUNTRY=US
#   HOTSPOT_CHANNEL=6
#   HOTSPOT_AP_IP=10.42.0.1
#   HOTSPOT_AP_CIDR=24
#   HOTSPOT_DHCP_START=10.42.0.50
#   HOTSPOT_DHCP_END=10.42.0.150
#   HOTSPOT_DHCP_LEASE=12h
#   HOTSPOT_APP_PORT=8080
#   HOTSPOT_ALLOW_SSH=true
#   HOTSPOT_SSH_PORT=22
#   PHOTOBOOTH_SERVICE=photobooth.service

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (sudo ./setup_pi_hotspot.sh)"
  exit 1
fi

HOTSPOT_IFACE="${HOTSPOT_IFACE:-wlan0}"
HOTSPOT_SSID="${HOTSPOT_SSID:-Photobooth}"
HOTSPOT_PSK="${HOTSPOT_PSK:-photobooth123}"
HOTSPOT_COUNTRY="${HOTSPOT_COUNTRY:-US}"
HOTSPOT_CHANNEL="${HOTSPOT_CHANNEL:-6}"
HOTSPOT_AP_IP="${HOTSPOT_AP_IP:-10.42.0.1}"
HOTSPOT_AP_CIDR="${HOTSPOT_AP_CIDR:-24}"
HOTSPOT_DHCP_START="${HOTSPOT_DHCP_START:-10.42.0.50}"
HOTSPOT_DHCP_END="${HOTSPOT_DHCP_END:-10.42.0.150}"
HOTSPOT_DHCP_LEASE="${HOTSPOT_DHCP_LEASE:-12h}"
HOTSPOT_APP_PORT="${HOTSPOT_APP_PORT:-8080}"
HOTSPOT_ALLOW_SSH="${HOTSPOT_ALLOW_SSH:-true}"
HOTSPOT_SSH_PORT="${HOTSPOT_SSH_PORT:-22}"
PHOTOBOOTH_SERVICE="${PHOTOBOOTH_SERVICE:-photobooth.service}"

if [[ "${#HOTSPOT_PSK}" -lt 8 || "${#HOTSPOT_PSK}" -gt 63 ]]; then
  echo "HOTSPOT_PSK must be 8-63 characters."
  exit 1
fi

if [[ "${HOTSPOT_ALLOW_SSH}" != "true" && "${HOTSPOT_ALLOW_SSH}" != "false" ]]; then
  echo "HOTSPOT_ALLOW_SSH must be 'true' or 'false'."
  exit 1
fi

if ! command -v iptables >/dev/null 2>&1; then
  echo "iptables not found. Please install iptables and retry."
  exit 1
fi

if ! ip link show "${HOTSPOT_IFACE}" >/dev/null 2>&1; then
  echo "Network interface not found: ${HOTSPOT_IFACE}"
  exit 1
fi

add_iptables_input_rule() {
  if ! iptables -C INPUT "$@" >/dev/null 2>&1; then
    iptables -A INPUT "$@"
  fi
}

add_iptables_nat_rule() {
  if ! iptables -t nat -C PREROUTING "$@" >/dev/null 2>&1; then
    iptables -t nat -A PREROUTING "$@"
  fi
}

echo "Installing hotspot packages (if missing)..."
MISSING_PACKAGES=()
for pkg in hostapd dnsmasq; do
  if ! dpkg -s "${pkg}" >/dev/null 2>&1; then
    MISSING_PACKAGES+=("${pkg}")
  fi
done

if [[ "${#MISSING_PACKAGES[@]}" -gt 0 ]]; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y "${MISSING_PACKAGES[@]}"
fi

echo "Writing hostapd config..."
cat > /etc/hostapd/hostapd.conf <<EOF
country_code=${HOTSPOT_COUNTRY}
interface=${HOTSPOT_IFACE}
ssid=${HOTSPOT_SSID}
hw_mode=g
channel=${HOTSPOT_CHANNEL}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${HOTSPOT_PSK}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
ieee80211n=1
wmm_enabled=1
EOF

if [[ -f /etc/default/hostapd ]]; then
  if grep -Eq '^#?DAEMON_CONF=' /etc/default/hostapd; then
    sed -i 's|^#\?DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
  else
    echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd
  fi
fi

echo "Writing dnsmasq captive DNS config..."
cat > /etc/dnsmasq.d/photobooth-hotspot.conf <<EOF
interface=${HOTSPOT_IFACE}
bind-interfaces
no-resolv
dhcp-range=${HOTSPOT_DHCP_START},${HOTSPOT_DHCP_END},255.255.255.0,${HOTSPOT_DHCP_LEASE}
dhcp-option=3,${HOTSPOT_AP_IP}
dhcp-option=6,${HOTSPOT_AP_IP}
address=/#/${HOTSPOT_AP_IP}
EOF

echo "Disabling hotspot service autostart (manual run required each boot)..."
systemctl disable hostapd >/dev/null 2>&1 || true
systemctl disable dnsmasq >/dev/null 2>&1 || true
systemctl disable netfilter-persistent >/dev/null 2>&1 || true

echo "Switching ${HOTSPOT_IFACE} into hotspot mode for this boot..."
systemctl stop wpa_supplicant.service >/dev/null 2>&1 || true
systemctl stop "wpa_supplicant@${HOTSPOT_IFACE}.service" >/dev/null 2>&1 || true
ip link set "${HOTSPOT_IFACE}" down
ip addr flush dev "${HOTSPOT_IFACE}"
ip addr add "${HOTSPOT_AP_IP}/${HOTSPOT_AP_CIDR}" dev "${HOTSPOT_IFACE}"
ip link set "${HOTSPOT_IFACE}" up

echo "Applying captive portal firewall rules..."
add_iptables_input_rule -i "${HOTSPOT_IFACE}" -p udp --dport 67 -j ACCEPT
add_iptables_input_rule -i "${HOTSPOT_IFACE}" -p udp --dport 53 -j ACCEPT
add_iptables_input_rule -i "${HOTSPOT_IFACE}" -p tcp --dport 53 -j ACCEPT
add_iptables_input_rule -i "${HOTSPOT_IFACE}" -p tcp --dport 80 -j ACCEPT
add_iptables_input_rule -i "${HOTSPOT_IFACE}" -p tcp --dport "${HOTSPOT_APP_PORT}" -j ACCEPT
if [[ "${HOTSPOT_ALLOW_SSH}" == "true" ]]; then
  add_iptables_input_rule -i "${HOTSPOT_IFACE}" -p tcp --dport "${HOTSPOT_SSH_PORT}" -j ACCEPT
fi
add_iptables_nat_rule -i "${HOTSPOT_IFACE}" -p tcp --dport 80 -j REDIRECT --to-ports "${HOTSPOT_APP_PORT}"

echo "Restarting services..."
systemctl unmask hostapd || true
systemctl restart dnsmasq
systemctl restart hostapd

if systemctl list-unit-files | grep -q "^${PHOTOBOOTH_SERVICE}"; then
  systemctl restart "${PHOTOBOOTH_SERVICE}" || true
fi

echo
echo "Hotspot ready."
echo "SSID: ${HOTSPOT_SSID}"
echo "Password: ${HOTSPOT_PSK}"
echo "Portal URL: http://${HOTSPOT_AP_IP}:${HOTSPOT_APP_PORT}"
if [[ "${HOTSPOT_ALLOW_SSH}" == "true" ]]; then
  echo "SSH: ssh <user>@${HOTSPOT_AP_IP} -p ${HOTSPOT_SSH_PORT}"
fi
echo "Autostart: disabled (run this script again after reboot to re-enable hotspot)"
echo
echo "On many phones, connecting to the hotspot will auto-open the captive portal."
echo "If it does not open, browse to http://neverssl.com once while connected."
