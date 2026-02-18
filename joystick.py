"""
Joystick Controller for Photobooth
Reads a USB joystick (DragonRise Inc.) via hidapi and triggers photo captures.
"""

import threading
import time


# DragonRise Inc. Generic USB Joystick
VENDOR_ID = 0x0079
PRODUCT_ID = 0x0006

# HID report byte/bit positions (byte 5 upper nibble holds K1-K4)
BUTTON_BYTE = 5
BUTTON_MASK = 0xF0  # upper nibble only; lower nibble is hat switch
K1_BIT = 4  # Single Photo  (0x0f → 0x1f)
K2_BIT = 5  # Photo Strip   (0x0f → 0x2f)

DEBOUNCE_SECONDS = 2.0
RECONNECT_INTERVAL = 3.0


class JoystickController:
    def __init__(self, on_single_photo=None, on_photo_strip=None):
        self.on_single_photo = on_single_photo
        self.on_photo_strip = on_photo_strip
        self._device = None
        self._running = False
        self._last_press_time = 0
        self._prev_buttons = 0  # previous button state for edge detection
        self._connected = False
        self._lock = threading.Lock()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._running = True
        self._thread.start()

    @property
    def connected(self):
        with self._lock:
            return self._connected

    def _connect(self):
        """Try to open the HID device. Returns True on success."""
        try:
            import hid
            device = hid.device()
            device.open(VENDOR_ID, PRODUCT_ID)
            device.set_nonblocking(True)
            self._device = device
            with self._lock:
                self._connected = True
            print("🕹️  Joystick connected")
            return True
        except Exception:
            self._device = None
            with self._lock:
                self._connected = False
            return False

    def _disconnect(self):
        """Close the device if open."""
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None
        with self._lock:
            self._connected = False

    def _run(self):
        """Main loop: connect, read, handle buttons, reconnect on failure."""
        while self._running:
            if not self._device:
                if not self._connect():
                    time.sleep(RECONNECT_INTERVAL)
                    continue

            try:
                data = self._device.read(64)
                if data and len(data) > BUTTON_BYTE:
                    self._handle_report(data)
                else:
                    # No data available (non-blocking), short sleep to avoid busy-wait
                    time.sleep(0.01)
            except Exception:
                # Device disconnected or read error
                print("🕹️  Joystick disconnected")
                self._disconnect()
                self._prev_buttons = 0
                time.sleep(RECONNECT_INTERVAL)

    def _handle_report(self, data):
        """Process a HID report, fire callbacks on button press edges."""
        # Mask to upper nibble only (ignore hat switch in lower nibble)
        buttons = data[BUTTON_BYTE] & BUTTON_MASK
        prev = self._prev_buttons
        self._prev_buttons = buttons

        # Edge detection: bits that just went from 0 to 1
        rising = buttons & ~prev

        if not rising:
            return

        now = time.time()
        if now - self._last_press_time < DEBOUNCE_SECONDS:
            return

        if rising & (1 << K1_BIT):
            self._last_press_time = now
            print("🕹️  K1 pressed → Single Photo")
            if self.on_single_photo:
                self.on_single_photo()
        elif rising & (1 << K2_BIT):
            self._last_press_time = now
            print("🕹️  K2 pressed → Photo Strip")
            if self.on_photo_strip:
                self.on_photo_strip()

    def stop(self):
        """Stop the background thread and close the device."""
        self._running = False
        self._disconnect()
