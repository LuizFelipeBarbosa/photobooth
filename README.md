# Photobooth 📷

Capture photos from your webcam and print them on a RONGTA thermal printer.

## Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# macOS only: Install libusb for USB printer support
brew install libusb
```

## Usage

### Take and Print a Photo

```bash
# With 3-second countdown
python photobooth.py

# Instant capture (no countdown)
python photobooth.py --countdown 0

# Use a different camera
python photobooth.py --camera 1
```

### Print a Custom Message

```python
from thermal_printer import print_message, print_receipt

# Simple message
print_message("Hello World!")

# Formatted receipt
print_receipt(
    title="PHOTOBOOTH",
    lines=["Line 1", "Line 2"],
    footer="Thanks!"
)
```

## Files

- `photobooth.py` - Main app (capture + print)
- `thermal_printer.py` - Printer utilities
- `photos/` - Saved photos

## Printer Info

- **Vendor ID:** `0x0fe6`
- **Product ID:** `0x811e`
- **Model:** RONGTA USB Receipt Printer

## Web Interface

Run the web server to control the photobooth from your phone:

```bash
python server.py
```

- **Local URL:** `http://localhost:8080`
- **Network URL:** The script will print a network URL (e.g., `http://192.168.1.5:8080`) that you can open on any device connected to the same Wi-Fi.

### Features
- **Single Photo:** Takes one photo and prints it instantly.
- **Photo Strip:** Takes 3 photos with a countdown and gap between each, stitches them into a strip, and prints it.
