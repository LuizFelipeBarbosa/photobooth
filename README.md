# Photobooth 📷

A web-based photobooth with React frontend, Flask backend, and thermal printer support. Perfect for parties and events!

## Features

- **Single Photo** - Capture one photo with countdown
- **Photo Strip** - Capture 3 photos and stitch them into a strip
- **Gallery** - Browse, like, reprint, and delete photos
- **Thermal Printing** - Automatic printing to RONGTA thermal printer
- **Mobile Friendly** - Control from any phone on your network

## Tech Stack

- **Frontend:** React + Tailwind CSS (Vite)
- **Backend:** Flask + Python
- **Camera:** OpenCV (USB webcam) or picamera2 (Raspberry Pi Camera)
- **Printer:** RONGTA USB thermal printer via python-escpos

## Quick Start

### Development (macOS)

```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Run development servers
python server.py                  # Backend on :8080
cd frontend && npm run dev        # Frontend on :5173 (proxies to backend)
```

### Production

```bash
cd frontend && npm run build      # Build React app
python server.py                  # Serves everything on :8080
```

## Raspberry Pi Deployment

See [DEPLOY.md](DEPLOY.md) for detailed instructions on deploying to a Raspberry Pi.

```bash
# Quick deploy from Mac
cd frontend && npm run build && cd ..
rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '.git' \
  ./ pi2@YOUR_PI_IP:~/photobooth/
ssh pi2@YOUR_PI_IP "sudo systemctl restart photobooth"
```

### Raspberry Pi Hotspot + Captive Portal

To let guests connect directly to the Pi and automatically land on the photobooth:

```bash
ssh pi2@YOUR_PI_IP
cd ~/photobooth
sudo HOTSPOT_SSID="Photobooth" HOTSPOT_PSK="change-me-now" ./setup_pi_hotspot.sh
```

After setup, connecting to the hotspot should open the captive portal and load the app on `http://10.42.0.1:8080`.
To SSH while on hotspot, connect to that Wi-Fi and use `ssh pi2@10.42.0.1`.
Hotspot autostart is intentionally disabled; reboot returns normal Wi-Fi/internet mode, and you re-run the script when you want hotspot mode again.

## Project Structure

```
photobooth/
├── frontend/           # React + Tailwind CSS app
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Home and Gallery pages
│   │   └── hooks/      # Custom React hooks
│   └── dist/           # Production build (served by Flask)
├── photos/             # Captured photos
├── server.py           # Flask API server
├── photobooth.py       # Camera capture logic
├── thermal_printer.py  # Printer utilities
└── requirements.txt    # Python dependencies
```

## API Endpoints

| Endpoint                  | Method | Description          |
| ------------------------- | ------ | -------------------- |
| `/api/photo`              | POST   | Take a single photo  |
| `/api/strip`              | POST   | Take a 3-photo strip |
| `/api/status`             | GET    | Get capture status   |
| `/api/photos`             | GET    | List all photos      |
| `/api/like/<filename>`    | POST   | Toggle like on photo |
| `/api/reprint/<filename>` | POST   | Reprint a photo      |
| `/api/delete/<filename>`  | POST   | Delete a photo       |

## Hardware

- **Printer:** RONGTA USB Receipt Printer (Vendor: `0x0fe6`, Product: `0x811e`)
- **Camera:** Any USB webcam or Raspberry Pi Camera Module

## License

MIT
