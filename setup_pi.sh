#!/bin/bash

# Setup script for Photobooth Auto-Start on Raspberry Pi

# 1. Check if running as root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root (sudo ./setup_pi.sh)"
  exit
fi

echo "📸 Setting up Photobooth Service..."

# 2. Update paths in service file if needed (optional dynamic replace, but keeping simple for now)
# We assume the user has cloned to /home/pi/photobooth as per standard pi setup.
# If current directory is different, warn user?
CURRENT_DIR=$(pwd)
if [[ "$CURRENT_DIR" != "/home/pi/photobooth" ]]; then
    echo "⚠️  Warning: Current directory is $CURRENT_DIR"
    echo "   The service file expects /home/pi/photobooth."
    echo "   If this is incorrect, please edit 'photobooth.service' before continuing."
    read -p "   Press ENTER to continue or Ctrl+C to cancel..."
fi

# 3. Copy service file to systemd directory
echo "Copying service file..."
cp photobooth.service /etc/systemd/system/photobooth.service

# 4. Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# 5. Enable service to start on boot
echo "Enabling service on boot..."
systemctl enable photobooth.service

# 6. Start the service now?
read -p "Do you want to start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Starting service..."
    systemctl start photobooth.service
    echo "Service started! Checking status..."
    systemctl status photobooth.service --no-pager
else
    echo "Service enabled but not started. Reboot or run 'sudo systemctl start photobooth.service' to start."
fi

echo "✅ Setup Complete!"
