#!/usr/bin/env bash
set -euo pipefail

# Configure Raspberry Pi as a standalone Wi-Fi hotspot + generate QR codes.
# Run this ON the Pi as root: sudo ./setup_pi_hotspot.sh
#
# Optional env overrides:
#   PB_SSID="Photobooth"
#   PB_PASS="your_password"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (sudo ./setup_pi_hotspot.sh)"
  exit 1
fi

SSID="${PB_SSID:-Photobooth}"
PASS="${PB_PASS:-}"
ADMIN_DIR="/home/pi2/photobooth/admin"
QR_DIR="/home/pi2/photobooth/qr"
GW_CIDR="10.42.0.1/24"
DHCP_RANGE="10.42.0.50,10.42.0.150,255.255.255.0,12h"

if [[ -z "${PASS}" ]]; then
  PASS="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-16)"
fi

install -d -m 700 "${ADMIN_DIR}"
printf "SSID=%s\nPASS=%s\n" "${SSID}" "${PASS}" | tee "${ADMIN_DIR}/ap-credentials.txt" >/dev/null
chmod 600 "${ADMIN_DIR}/ap-credentials.txt"

use_nm="false"
if command -v nmcli >/dev/null 2>&1 && systemctl is-active --quiet NetworkManager; then
  use_nm="true"
fi

if [[ "${use_nm}" == "true" ]]; then
  echo "Using NetworkManager to configure AP..."
  if nmcli con show PhotoboothAP >/dev/null 2>&1; then
    nmcli con delete PhotoboothAP
  fi
  nmcli con add type wifi ifname wlan0 con-name PhotoboothAP ssid "${SSID}"
  nmcli con modify PhotoboothAP 802-11-wireless.mode ap 802-11-wireless.band bg
  nmcli con modify PhotoboothAP ipv4.addresses "${GW_CIDR}" ipv4.method shared
  nmcli con modify PhotoboothAP ipv6.method ignore
  nmcli con modify PhotoboothAP wifi-sec.key-mgmt wpa-psk wifi-sec.psk "${PASS}"
  nmcli con modify PhotoboothAP connection.autoconnect yes
  nmcli con up PhotoboothAP
else
  echo "Using hostapd + dnsmasq to configure AP..."
  apt-get update
  apt-get install -y hostapd dnsmasq qrencode

  DHCPCD_CONF="/etc/dhcpcd.conf"
  if ! grep -q "photobooth-hotspot-start" "${DHCPCD_CONF}"; then
    cat >> "${DHCPCD_CONF}" <<EOF
# photobooth-hotspot-start
interface wlan0
static ip_address=10.42.0.1/24
nohook wpa_supplicant
# photobooth-hotspot-end
EOF
  fi

  cat > /etc/hostapd/hostapd.conf <<EOF
country_code=US
interface=wlan0
ssid=${SSID}
hw_mode=g
channel=6
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=${PASS}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

  if [[ -f /etc/default/hostapd ]]; then
    sed -i.bak -e 's|^#\\?DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
  fi

  cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
dhcp-range=${DHCP_RANGE}
dhcp-option=3,10.42.0.1
dhcp-option=6,10.42.0.1
EOF

  systemctl restart dhcpcd
  systemctl unmask hostapd
  systemctl enable --now hostapd dnsmasq
fi

if ! command -v qrencode >/dev/null 2>&1; then
  apt-get update
  apt-get install -y qrencode
fi

install -d -m 755 "${QR_DIR}"
qrencode -o "${QR_DIR}/wifi.png" "WIFI:T:WPA;S:${SSID};P:${PASS};H:false;;"
qrencode -o "${QR_DIR}/app.png" "http://10.42.0.1:8080"

cat > "${QR_DIR}/index.html" <<'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Photobooth QR Codes</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 24px; }
      h1 { margin-bottom: 12px; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 24px; }
      .card { border: 1px solid #ddd; border-radius: 12px; padding: 16px; text-align: center; }
      img { max-width: 200px; width: 100%; height: auto; }
      .label { margin-top: 8px; font-weight: 600; }
    </style>
  </head>
  <body>
    <h1>Photobooth QR Codes</h1>
    <div class="grid">
      <div class="card">
        <img src="wifi.png" alt="Wi-Fi QR" />
        <div class="label">Join Wi-Fi</div>
      </div>
      <div class="card">
        <img src="app.png" alt="App QR" />
        <div class="label">Open App</div>
      </div>
    </div>
  </body>
</html>
EOF

echo "Hotspot configured."
echo "SSID: ${SSID}"
echo "Password stored at: ${ADMIN_DIR}/ap-credentials.txt"
echo "QR codes at: ${QR_DIR}/wifi.png and ${QR_DIR}/app.png"
