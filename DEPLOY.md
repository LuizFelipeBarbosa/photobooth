# Deploying Updates to Raspberry Pi

This guide explains how to update the photobooth on your Raspberry Pi after making changes on your development machine.

## Prerequisites

- Development machine with Node.js and npm installed
- SSH access to Raspberry Pi (pi2@10.0.0.71)
- `sshpass` installed for scripted deployments (optional)

## Quick Deploy Script

Run this from the project root on your Mac:

```bash
# 1. Build the React frontend
cd frontend && npm run build && cd ..

# 2. Copy updated files to Pi (excludes venv, node_modules)
rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '.git' \
  ./ pi2@10.0.0.71:~/photobooth/

# 3. Restart the service
ssh pi2@10.0.0.71 "sudo systemctl restart photobooth"
```

## Step-by-Step Instructions

### 1. Build the Frontend

After making changes to React components:

```bash
cd /Users/lfpmb/Desktop/GitHub-Repos/photobooth/frontend
npm run build
```

This creates/updates the `frontend/dist` folder with production-ready files.

### 2. Transfer Files to Pi

**Option A: Using rsync (recommended)**
```bash
rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '.git' \
  /Users/lfpmb/Desktop/GitHub-Repos/photobooth/ pi2@10.0.0.71:~/photobooth/
```

**Option B: Using scp**
```bash
scp -r /Users/lfpmb/Desktop/GitHub-Repos/photobooth/frontend/dist \
  pi2@10.0.0.71:~/photobooth/frontend/
```

### 3. Restart the Service

```bash
ssh pi2@10.0.0.71 "sudo systemctl restart photobooth"
```

### 4. Verify the Update

Check service status:
```bash
ssh pi2@10.0.0.71 "sudo systemctl status photobooth"
```

View logs:
```bash
ssh pi2@10.0.0.71 "sudo journalctl -u photobooth -f"
```

Access the app at: http://10.0.0.71:8080

## Configure Guest Wi-Fi + Captive Portal

If you want guests to connect directly to the Pi instead of venue Wi-Fi:

```bash
ssh pi2@YOUR_PI_IP
cd ~/Documents/photobooth
sudo ./setup_pi_hotspot.sh
```

What this configures:
- Wi-Fi hotspot on `wlan0` (default SSID `Photobooth`)
- Gateway at `10.42.0.1`
- QR codes in `/home/pi2/photobooth/qr`
- Captive portal redirect on port `80` to `http://10.42.0.1:8080`

Check status:

```bash
sudo systemctl status photobooth-captive-portal --no-pager
sudo ss -ltnp | grep ':80'
```

## Updating Python Dependencies

If you add new Python packages:

```bash
ssh pi2@10.0.0.71
cd ~/photobooth
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart photobooth
```

## Troubleshooting

| Issue               | Solution                                           |
| ------------------- | -------------------------------------------------- |
| Service won't start | Check logs: `sudo journalctl -u photobooth -n 50`  |
| Camera not detected | Ensure camera is connected, check `ls /dev/video*` |
| Printer not working | Check USB connection: `lsusb`                      |
| Changes not visible | Clear browser cache or hard refresh (Ctrl+Shift+R) |
