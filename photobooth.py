"""
Photobooth - Capture and Print
Takes a photo from webcam/Pi Camera and prints it on RONGTA thermal printer

Supports:
- Raspberry Pi Camera Module (via picamera2)
- USB webcams (via OpenCV)
- Automatic detection of available camera
"""

import os
import sys
import time
from datetime import datetime
from PIL import Image

# Set library path for libusb on macOS (Homebrew)
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

from escpos.printer import Usb


# RONGTA Printer settings (detected from your printer)
VENDOR_ID = 0x0fe6
PRODUCT_ID = 0x811e

# Photo output directory
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

# Import Camera Libraries
PICAMERA_AVAILABLE = False
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
    print("✅ Pi Camera support available")
except ImportError:
    pass

OPENCV_AVAILABLE = False
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    print("⚠️ OpenCV not available")


import threading

class PhotoboothCamera:
    def __init__(self, camera_type='auto', width=1920, height=1080, headless=False):
        self.width = width
        self.height = height
        self.headless = headless
        self.camera_type = self._detect_camera(camera_type)
        
        self.picam = None
        self.cap = None
        
        # Threading support
        self.stopped = False
        self.lock = threading.Lock()
        self._frame = None
        self.thread = None
        
        self._initialize_camera()

    def _detect_camera(self, requested_type):
        if requested_type == 'picamera':
            if PICAMERA_AVAILABLE:
                return 'picamera'
            else:
                print("⚠️ picamera2 not installed, falling back to OpenCV")
                return 'opencv'
        elif requested_type == 'opencv':
            return 'opencv'
        else:  # auto
            if PICAMERA_AVAILABLE:
                try:
                    # quick check
                    picam = Picamera2()
                    picam.close()
                    print("📷 Detected: Pi Camera")
                    return 'picamera'
                except:
                    pass
            
            if OPENCV_AVAILABLE:
                print("📷 Using: OpenCV (USB webcam)")
                return 'opencv'
            
            raise RuntimeError("No camera available!")

    def _initialize_camera(self):
        print(f"📷 Initializing {self.camera_type} camera ({self.width}x{self.height})...")
        
        if self.camera_type == 'picamera':
            self.picam = Picamera2()
            config = self.picam.create_still_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                buffer_count=2
            )
            self.picam.configure(config)
            self.picam.start()
            # Warmup
            print("📷 Adjusting white balance and exposure...")
            time.sleep(2.0)

            # Start background frame-grabbing thread (matches OpenCV pattern)
            self.stopped = False
            self.thread = threading.Thread(target=self._update_picamera, daemon=True)
            self.thread.start()
            time.sleep(0.5)  # Wait for first frame

        elif self.camera_type == 'opencv':
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Could not open OpenCV camera")
            
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Start background thread for OpenCV
            self.stopped = False
            self.thread = threading.Thread(target=self._update_opencv, args=())
            self.thread.daemon = True
            self.thread.start()
            
            # Wait for first frame
            print("📷 Waiting for first frame...")
            time.sleep(1.0)
            
        print("📷 Camera ready and persistent!")

    def _update_picamera(self):
        """Background thread to continuously grab frames from PiCamera."""
        print("📷 PiCamera thread started")
        while not self.stopped:
            try:
                array = self.picam.capture_array("main")
                if array is not None:
                    with self.lock:
                        self._frame = array
            except Exception:
                time.sleep(0.1)
        print("📷 PiCamera thread stopped")

    def get_frame(self):
        """Return the latest frame (numpy array) or None."""
        with self.lock:
            if self._frame is not None:
                return self._frame.copy()
        return None

    def _update_opencv(self):
        """Background thread to continuously grab frames from OpenCV."""
        print("📷 Camera thread started")
        while not self.stopped:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self._frame = frame
                else:
                    # If we lost the camera, maybe try to reconnect?
                    # For now just sleep a bit to avoid CPU spin
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        print("📷 Camera thread stopped")

    def close(self):
        self.stopped = True
        if self.thread:
            self.thread.join()
            
        if self.picam:
            self.picam.stop()
            self.picam.close()
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()

    def capture(self, countdown=0, filename_prefix="photo"):
        # Handle countdown (blocking, for sync)
        if countdown > 0:
            print(f"📷 Waiting {countdown}s...")
            time.sleep(countdown)
            
        print("📸 SNAP!")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)

        if self.camera_type == 'picamera':
            # Grab latest frame from background thread
            frame = None
            with self.lock:
                if self._frame is not None:
                    frame = self._frame.copy()

            if frame is None:
                print("❌ Failed to capture photo (no frame in buffer)")
                return None

            img = Image.fromarray(frame)
            img.save(filepath, "JPEG", quality=95)
            
        elif self.camera_type == 'opencv':
            # Grab latest frame from thread
            frame = None
            with self.lock:
                if self._frame is not None:
                    frame = self._frame.copy()
            
            if frame is None:
                print("❌ Failed to capture photo (no frame in buffer)")
                return None
            
            # Flash effect (optional, only if not headless)
            if not self.headless:
                try:
                    white = frame.copy()
                    white[:] = (255, 255, 255)
                    cv2.imshow("Photobooth", white)
                    cv2.waitKey(50)
                except: pass
                
            cv2.imwrite(filepath, frame)
            
        print(f"✅ Photo captured: {filepath}")
        return filepath

    def capture_strip(self, num_photos=3, countdown=3, gap=2):
        photo_paths = []
        
        for i in range(num_photos):
            if i > 0:
                print(f"⏳ Gap: {gap}s...")
                time.sleep(gap)
                
            print(f"\n📸 Strip Photo {i+1}/{num_photos}")
            # Ensure full countdown for every photo so users can prep
            path = self.capture(countdown, filename_prefix="strip")
            if path:
                photo_paths.append(path)
                
        return photo_paths


# --- Logic for Processing & Printing (Stateless) ---

def process_for_thermal(image_path, is_strip=False):
    """Process an image for optimal thermal printer output."""
    from PIL import ImageEnhance, ImageFilter
    
    img = Image.open(image_path)
    thermal_width = 576
    
    if not is_strip:
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        img = img.crop((left, top, right, bottom))
        img = img.resize((thermal_width, thermal_width), Image.Resampling.LANCZOS)
    else:
        aspect = img.height / img.width
        new_height = int(thermal_width * aspect)
        img = img.resize((thermal_width, new_height), Image.Resampling.LANCZOS)
    
    img = img.convert('L')
    img = img.filter(ImageFilter.SMOOTH)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    
    processed_path = image_path.replace('.jpg', '_thermal.png')
    img.save(processed_path)
    return processed_path

def print_photo(image_path):
    """Print a photo to the thermal printer."""
    print("🖨️ Connecting to printer...")
    try:
        printer = Usb(VENDOR_ID, PRODUCT_ID, 0)
        printer.set(align='center', bold=True, double_height=True, double_width=True)
        printer.text("THE OCHO\n")
        printer.set(align='center', bold=False, double_height=False, double_width=False)
        printer.text("PHOTOBOOTH\n")
        
        printer.set(align='center', font='b')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        printer.text(f"{timestamp}\n")
        printer.set(font='a')
        printer.text("\n")
        
        print("🖨️ Printing image...")
        printer.image(image_path, impl="bitImageColumn")
        
        printer.text("\n")
        printer.set(align='center')
        printer.text("Thanks for visiting!\n")
        printer.text("\n\n\n")
        printer.cut()
        printer.close()
        print("✅ Print complete!")
        return True
    except Exception as e:
        print(f"❌ Print error: {e}")
        return False

def create_photo_strip(photo_paths, spacing=20):
    """Combine multiple photos into a vertical strip."""
    if not photo_paths: return None
    
    images = [Image.open(p) for p in photo_paths]
    target_width = 576
    resized = []
    
    for img in images:
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        img = img.crop((left, top, right, bottom))
        resized.append(img.resize((target_width, target_width), Image.Resampling.LANCZOS))
    
    total_height = sum(img.height for img in resized) + spacing * (len(resized) - 1)
    strip = Image.new('RGB', (target_width, total_height), 'white')
    
    y_offset = 0
    for img in resized:
        strip.paste(img, (0, y_offset))
        y_offset += img.height + spacing
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    strip_path = os.path.join(PHOTOS_DIR, f"photostrip_{timestamp}.jpg")
    strip.save(strip_path, quality=95)
    return strip_path

# --- Main CLI entry (Legacy/Standalone support) ---

def run_standalone():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--countdown", type=int, default=3)
    parser.add_argument("--strip", action="store_true")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    
    cam = PhotoboothCamera(headless=args.headless)
    
    try:
        if args.strip:
            paths = cam.capture_strip(countdown=args.countdown)
            strip_path = create_photo_strip(paths)
            if strip_path:
                thermal = process_for_thermal(strip_path, True)
                print_photo(thermal)
        else:
            path = cam.capture(countdown=args.countdown)
            if path:
                thermal = process_for_thermal(path)
                print_photo(thermal)
    finally:
        cam.close()

if __name__ == "__main__":
    run_standalone()
