"""
Photobooth Kiosk Mode
Fullscreen OpenCV display with joystick-only input.
Mutually exclusive with the web server (server.py).
"""

import os
import sys
import time
import threading
import numpy as np

# Set library path for libusb on macOS (Homebrew)
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

import cv2
from photobooth import PhotoboothCamera, process_for_thermal, print_photo, create_photo_strip

# ── State constants ──
IDLE = "IDLE"
COUNTDOWN = "COUNTDOWN"
FLASH = "FLASH"
CAPTURE = "CAPTURE"
STRIP_GAP = "STRIP_GAP"
REVIEW = "REVIEW"
PRINTING = "PRINTING"

# ── Timing constants (seconds) ──
COUNTDOWN_SECONDS = 3
FLASH_DURATION = 0.2
REVIEW_DURATION = 4
STRIP_GAP_DURATION = 2
STRIP_NUM_PHOTOS = 3

WINDOW_NAME = "Photobooth"


class KioskApp:
    def __init__(self):
        # Camera (headless — we manage our own OpenCV window)
        self.camera = PhotoboothCamera(headless=True)

        # State
        self.state = IDLE
        self.state_start = time.time()
        self.is_strip = False
        self.strip_photo_index = 0
        self.strip_paths = []
        self.countdown_number = COUNTDOWN_SECONDS
        self.review_image = None

        # Joystick thread-safe action queue
        self._pending_action = None
        self._action_lock = threading.Lock()

        # Printing
        self._print_done = False

        # Detect screen resolution
        self.screen_w, self.screen_h = self._detect_screen_size()

        # Window — force fullscreen by positioning and resizing explicitly
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow(WINDOW_NAME, 0, 0)
        cv2.resizeWindow(WINDOW_NAME, self.screen_w, self.screen_h)
        # Show a blank frame so the window manager registers the window
        cv2.imshow(WINDOW_NAME, np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8))
        cv2.waitKey(100)
        self._force_fullscreen()

        # Joystick
        self.joystick = None
        self._init_joystick()

    def _force_fullscreen(self):
        """Use xdotool to remove decorations and force true fullscreen."""
        try:
            import subprocess
            wid = subprocess.check_output(
                ["xdotool", "search", "--name", WINDOW_NAME],
                stderr=subprocess.DEVNULL, text=True
            ).strip().splitlines()[0]
            # Set override-redirect so the WM ignores this window (no title bar)
            subprocess.run(["xdotool", "set_window", "--overrideredirect", "1", wid],
                           stderr=subprocess.DEVNULL)
            # Unmap/remap so the flag takes effect
            subprocess.run(["xdotool", "windowunmap", wid], stderr=subprocess.DEVNULL)
            time.sleep(0.3)
            subprocess.run(["xdotool", "windowmap", wid], stderr=subprocess.DEVNULL)
            subprocess.run(["xdotool", "windowmove", wid, "0", "0"],
                           stderr=subprocess.DEVNULL)
            subprocess.run(["xdotool", "windowsize", wid,
                            str(self.screen_w), str(self.screen_h)],
                           stderr=subprocess.DEVNULL)
            subprocess.run(["xdotool", "windowactivate", wid],
                           stderr=subprocess.DEVNULL)
            subprocess.run(["xdotool", "windowfocus", wid],
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️  Could not force fullscreen: {e}")

    @staticmethod
    def _detect_screen_size():
        """Return (width, height) of the primary screen."""
        try:
            import subprocess
            out = subprocess.check_output(
                ["xrandr"], stderr=subprocess.DEVNULL, text=True
            )
            for line in out.splitlines():
                if "*" in line:
                    res = line.split()[0]
                    w, h = res.split("x")
                    return int(w), int(h)
        except Exception:
            pass
        return 1920, 1080

    def _init_joystick(self):
        try:
            from joystick import JoystickController
            self.joystick = JoystickController(
                on_single_photo=lambda: self._queue_action("single"),
                on_photo_strip=lambda: self._queue_action("strip"),
            )
            print("🕹️  Joystick controller started")
        except Exception as e:
            print(f"🕹️  Joystick not available: {e}")

    def _queue_action(self, action):
        with self._action_lock:
            self._pending_action = action

    def _pop_action(self):
        with self._action_lock:
            action = self._pending_action
            self._pending_action = None
            return action

    # ── State transitions ──

    def _enter_state(self, state):
        self.state = state
        self.state_start = time.time()

    def _elapsed(self):
        return time.time() - self.state_start

    def _start_countdown(self):
        self.countdown_number = COUNTDOWN_SECONDS
        self._enter_state(COUNTDOWN)

    def _do_capture(self):
        """Grab a frame and save it. Runs in the main loop context."""
        self._enter_state(CAPTURE)
        filepath = self.camera.capture(countdown=0,
                                       filename_prefix="strip" if self.is_strip else "photo")
        return filepath

    def _start_printing(self, image_path, is_strip=False):
        self._print_done = False
        self._enter_state(PRINTING)

        def _print_thread():
            try:
                thermal = process_for_thermal(image_path, is_strip=is_strip)
                print_photo(thermal)
            except Exception as e:
                print(f"❌ Print error: {e}")
            finally:
                self._print_done = True

        threading.Thread(target=_print_thread, daemon=True).start()

    # ── Overlay helpers ──

    @staticmethod
    def _draw_text_centered(frame, text, y_ratio, font_scale, color=(255, 255, 255),
                            thickness=3, shadow=True):
        """Draw text centered horizontally at y_ratio (0.0-1.0) of frame height."""
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        x = (w - text_size[0]) // 2
        y = int(h * y_ratio) + text_size[1] // 2
        if shadow:
            cv2.putText(frame, text, (x + 2, y + 2), font, font_scale, (0, 0, 0), thickness + 2)
        cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)

    @staticmethod
    def _draw_banner(frame, text, y_ratio, font_scale=1.2, color=(255, 255, 255)):
        """Draw text on a semi-transparent dark banner."""
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

        banner_h = text_size[1] + 40
        y_top = int(h * y_ratio) - banner_h // 2
        y_top = max(0, min(y_top, h - banner_h))

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, y_top), (w, y_top + banner_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        x = (w - text_size[0]) // 2
        y = y_top + banner_h // 2 + text_size[1] // 2
        cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)

    # ── Main loop ──

    def run(self):
        print("\n" + "=" * 50)
        print("   PHOTOBOOTH KIOSK MODE")
        print("   Press ESC to exit")
        print("=" * 50 + "\n")

        try:
            while True:
                display = self._build_frame()
                if display is not None:
                    cv2.imshow(WINDOW_NAME, display)

                key = cv2.waitKey(16) & 0xFF
                if key == 27:  # ESC
                    break

                self._tick()
        finally:
            self._cleanup()

    def _build_frame(self):
        """Compose the display frame based on current state."""

        if self.state == FLASH:
            white = np.full((self.screen_h, self.screen_w, 3), 255, dtype=np.uint8)
            return white

        if self.state == REVIEW or self.state == PRINTING:
            return self._build_review_frame()

        # All other states show live mirrored preview
        frame = self.camera.get_frame()
        if frame is None:
            blank = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)
            self._draw_text_centered(blank, "Waiting for camera...", 0.5, 1.5)
            return blank

        # Mirror for selfie view
        frame = cv2.flip(frame, 1)

        if self.state == IDLE:
            self._draw_banner(frame, "Press the button to take a photo!", 0.85, 1.2)

        elif self.state == COUNTDOWN:
            elapsed = self._elapsed()
            remaining = COUNTDOWN_SECONDS - int(elapsed)
            if remaining < 1:
                remaining = 1
            self._draw_text_centered(frame, str(remaining), 0.45, 8.0,
                                     color=(0, 255, 255), thickness=12)
            if self.is_strip:
                label = f"Photo {self.strip_photo_index + 1}/{STRIP_NUM_PHOTOS}"
                self._draw_banner(frame, label, 0.15, 1.0)

        elif self.state == STRIP_GAP:
            label = f"Get ready for photo {self.strip_photo_index + 1}/{STRIP_NUM_PHOTOS}..."
            self._draw_banner(frame, label, 0.5, 1.2)

        elif self.state == CAPTURE:
            self._draw_text_centered(frame, "SNAP!", 0.5, 4.0, color=(0, 255, 255), thickness=8)

        return frame

    def _build_review_frame(self):
        """Show the captured photo centered on a dark background."""
        if self.review_image is None:
            blank = np.zeros((self.screen_h, self.screen_w, 3), dtype=np.uint8)
            self._draw_text_centered(blank, "Processing...", 0.5, 2.0)
            return blank

        review = self.review_image
        rh, rw = review.shape[:2]

        # Target display size: fit within screen
        screen_h, screen_w = self.screen_h, self.screen_w
        scale = min(screen_w / rw, screen_h / rh) * 0.85
        new_w = int(rw * scale)
        new_h = int(rh * scale)
        resized = cv2.resize(review, (new_w, new_h))

        canvas = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
        x_off = (screen_w - new_w) // 2
        y_off = (screen_h - new_h) // 2
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized

        if self.state == PRINTING:
            self._draw_banner(canvas, "Printing...", 0.9, 1.5)

        return canvas

    def _tick(self):
        """Process state timeouts and pending actions."""
        elapsed = self._elapsed()

        if self.state == IDLE:
            action = self._pop_action()
            if action == "single":
                self.is_strip = False
                self.strip_paths = []
                self._start_countdown()
            elif action == "strip":
                self.is_strip = True
                self.strip_photo_index = 0
                self.strip_paths = []
                self._start_countdown()

        elif self.state == COUNTDOWN:
            if elapsed >= COUNTDOWN_SECONDS:
                self._enter_state(FLASH)

        elif self.state == FLASH:
            if elapsed >= FLASH_DURATION:
                filepath = self._do_capture()
                if self.is_strip:
                    if filepath:
                        self.strip_paths.append(filepath)
                    self.strip_photo_index += 1
                    if self.strip_photo_index < STRIP_NUM_PHOTOS:
                        self._enter_state(STRIP_GAP)
                    else:
                        # Stitch strip and go to review
                        self._finish_strip()
                else:
                    self._finish_single(filepath)

        elif self.state == CAPTURE:
            # Capture is instant — handled in FLASH transition
            pass

        elif self.state == STRIP_GAP:
            if elapsed >= STRIP_GAP_DURATION:
                self._start_countdown()

        elif self.state == REVIEW:
            if elapsed >= REVIEW_DURATION:
                self._start_printing_current()

        elif self.state == PRINTING:
            if self._print_done:
                self._enter_state(IDLE)

    def _finish_single(self, filepath):
        """After single capture: load review image, enter REVIEW."""
        if filepath:
            img = cv2.imread(filepath)
            self.review_image = img
            self._current_print_path = filepath
            self._current_is_strip = False
        else:
            self.review_image = None
            self._current_print_path = None
        self._enter_state(REVIEW)

    def _finish_strip(self):
        """After all strip photos captured: stitch, load review, enter REVIEW."""
        if self.strip_paths:
            strip_path = create_photo_strip(self.strip_paths)
            if strip_path:
                img = cv2.imread(strip_path)
                self.review_image = img
                self._current_print_path = strip_path
                self._current_is_strip = True
            else:
                self.review_image = None
                self._current_print_path = None
        else:
            self.review_image = None
            self._current_print_path = None
        self._enter_state(REVIEW)

    def _start_printing_current(self):
        """Transition from REVIEW to PRINTING."""
        if self._current_print_path:
            self._start_printing(self._current_print_path, is_strip=self._current_is_strip)
        else:
            self._enter_state(IDLE)

    def _cleanup(self):
        print("Shutting down kiosk...")
        if self.joystick:
            self.joystick.stop()
        self.camera.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = KioskApp()
    app.run()
