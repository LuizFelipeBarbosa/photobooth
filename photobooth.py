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

# Headless mode (no GUI windows)
HEADLESS = False

# Camera type: 'auto', 'picamera', or 'opencv'
CAMERA_TYPE = 'auto'

# Try to import picamera2 (Raspberry Pi Camera)
PICAMERA_AVAILABLE = False
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
    print("✅ Pi Camera support available")
except ImportError:
    pass

# Import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️ OpenCV not available")


def detect_camera():
    """Detect which camera to use."""
    global CAMERA_TYPE
    
    if CAMERA_TYPE == 'picamera':
        if PICAMERA_AVAILABLE:
            return 'picamera'
        else:
            print("⚠️ picamera2 not installed, falling back to OpenCV")
            return 'opencv'
    elif CAMERA_TYPE == 'opencv':
        return 'opencv'
    else:  # auto
        # Check if we're on a Raspberry Pi with Pi Camera
        if PICAMERA_AVAILABLE:
            try:
                # Try to detect Pi Camera
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


def capture_photo_picamera(countdown=3, width=1920, height=1080):
    """Capture a photo using Pi Camera with proper AWB and exposure."""
    print(f"📷 Initializing Pi Camera ({width}x{height})...")
    
    picam = Picamera2()
    
    # Configure directly for still capture at requested resolution
    # Don't use preview mode - start directly in still mode
    config = picam.create_still_configuration(
        main={"size": (width, height), "format": "RGB888"},
        buffer_count=2
    )
    
    print(f"📷 Configuring for {width}x{height}...")
    picam.configure(config)
    
    # Verify configuration
    print(f"📷 Main stream size: {picam.camera_configuration()['main']['size']}")
    
    picam.start()
    
    # Wait for AWB and AE to converge (critical for good colors!)
    print("📷 Adjusting white balance and exposure...")
    time.sleep(2.5)
    print("📷 Pi Camera ready!")
    
    if countdown > 0:
        print(f"📷 Get ready! Taking photo in {countdown} seconds...")
        for i in range(countdown, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
    
    # Capture at full resolution using capture_array
    print("📸 Smile!")
    
    # Use capture_array to get the raw image data
    array = picam.capture_array("main")
    print(f"📷 Captured array shape: {array.shape}")
    
    picam.stop()
    picam.close()
    
    # Convert to PIL Image and save
    from PIL import Image as PILImage
    img = PILImage.fromarray(array)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.jpg"
    filepath = os.path.join(PHOTOS_DIR, filename)
    
    img.save(filepath, "JPEG", quality=95)
    print(f"✅ Photo saved: {filepath} ({img.size[0]}x{img.size[1]})")
    
    return filepath


def capture_photo_opencv(camera_index=0, countdown=3, width=1920, height=1080):
    """Capture a photo using OpenCV (USB webcam)."""
    print(f"📷 Initializing camera ({width}x{height})...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("❌ Could not open camera")
        return None
    
    # Force MJPG to enable higher resolutions on Pi
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    
    # Set higher resolution if supported
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Verify what we actually got
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"📷 Actual resolution: {int(actual_width)}x{int(actual_height)}")
    
    print("📷 Camera ready!")
    
    if countdown > 0:
        print(f"📷 Get ready! Taking photo in {countdown} seconds...")
        
        if HEADLESS:
            # Headless mode: just wait without GUI
            time.sleep(countdown)
        else:
            # Show preview with countdown
            start_time = cv2.getTickCount()
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                remaining = countdown - int(elapsed)
                
                if remaining <= 0:
                    break
                
                # Add countdown overlay
                display_frame = frame.copy()
                h, w = display_frame.shape[:2]
                
                # Draw countdown number
                font = cv2.FONT_HERSHEY_SIMPLEX
                text = str(remaining)
                text_size = cv2.getTextSize(text, font, 5, 10)[0]
                text_x = (w - text_size[0]) // 2
                text_y = (h + text_size[1]) // 2
                
                cv2.putText(display_frame, text, (text_x, text_y), font, 5, (255, 255, 255), 10)
                cv2.putText(display_frame, text, (text_x, text_y), font, 5, (0, 120, 255), 5)
                
                cv2.imshow("Photobooth - Get Ready!", display_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return None
    
    # Capture the actual photo
    print("📸 Smile!")
    ret, frame = cap.read()
    
    # Flash white!
    if ret and not HEADLESS:
        try:
            white_frame = frame.copy()
            white_frame[:] = (255, 255, 255)
            cv2.imshow("Photobooth - Get Ready!", white_frame)
            cv2.waitKey(150)  # Flash duration
        except:
            pass
    
    cap.release()
    if not HEADLESS:
        cv2.destroyAllWindows()
    
    if not ret:
        print("❌ Failed to capture photo")
        return None
    
    # Save the photo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.jpg"
    filepath = os.path.join(PHOTOS_DIR, filename)
    
    cv2.imwrite(filepath, frame)
    print(f"✅ Photo saved: {filepath}")
    
    return filepath


def capture_photo(camera_index=0, countdown=3, width=1920, height=1080):
    """Capture a photo using the best available camera."""
    camera_type = detect_camera()
    
    if camera_type == 'picamera':
        return capture_photo_picamera(countdown, width, height)
    else:
        return capture_photo_opencv(camera_index, countdown, width, height)


def capture_photo_strip_picamera(num_photos=3, countdown=3, width=1920, height=1080):
    """Capture multiple photos for a photo strip using Pi Camera."""
    from PIL import Image as PILImage
    
    print(f"📷 Initializing Pi Camera for {num_photos} photos ({width}x{height})...")
    
    picam = Picamera2()
    
    # Configure directly for still capture at requested resolution
    config = picam.create_still_configuration(
        main={"size": (width, height), "format": "RGB888"},
        buffer_count=2
    )
    
    print(f"📷 Configuring for {width}x{height}...")
    picam.configure(config)
    
    # Verify configuration
    print(f"📷 Main stream size: {picam.camera_configuration()['main']['size']}")
    
    picam.start()
    
    # Wait for AWB and AE to converge
    print("📷 Adjusting white balance and exposure...")
    time.sleep(2.5)
    print("📷 Pi Camera ready!")
    
    photo_paths = []
    
    for i in range(num_photos):
        print(f"\n📸 Photo {i + 1} of {num_photos}")
        
        if countdown > 0:
            print(f"   Get ready in {countdown}...")
            for j in range(countdown, 0, -1):
                print(f"   {j}...")
                time.sleep(1)
        
        print("   📸 Smile!")
        
        # Capture using capture_array for full resolution
        array = picam.capture_array("main")
        print(f"   📷 Captured array shape: {array.shape}")
        
        # Convert to PIL and save
        img = PILImage.fromarray(array)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strip_{timestamp}_{i+1}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)
        
        img.save(filepath, "JPEG", quality=95)
        photo_paths.append(filepath)
        print(f"   ✅ Captured! ({img.size[0]}x{img.size[1]})")
        
        # Short pause between photos
        if i < num_photos - 1:
            time.sleep(0.5)
    
    picam.stop()
    picam.close()
    
    return photo_paths


def capture_photo_strip_opencv(camera_index=0, num_photos=3, countdown=3, width=1920, height=1080):
    """Capture multiple photos for a photo strip using OpenCV."""
    print(f"📷 Photo strip mode: {num_photos} photos ({width}x{height})")
    print("📷 Initializing camera...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("❌ Could not open camera")
        return []
    
    # Force MJPG to enable higher resolutions on Pi
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Verify what we actually got
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"📷 Actual resolution: {int(actual_width)}x{int(actual_height)}")
    
    photo_paths = []
    
    for i in range(num_photos):
        print(f"\n📸 Photo {i + 1} of {num_photos}")
        
        if countdown > 0:
            print(f"   Get ready in {countdown}...")
            
            if HEADLESS:
                # Headless mode: just wait without GUI
                time.sleep(countdown)
            else:
                start_time = cv2.getTickCount()
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                    remaining = countdown - int(elapsed)
                    
                    if remaining <= 0:
                        break
                    
                    # Add countdown overlay
                    display_frame = frame.copy()
                    h, w = display_frame.shape[:2]
                    
                    # Photo number indicator
                    cv2.putText(display_frame, f"Photo {i+1}/{num_photos}", (20, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
                    cv2.putText(display_frame, f"Photo {i+1}/{num_photos}", (20, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 120, 255), 2)
                    
                    # Countdown number
                    text = str(remaining)
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 5, 10)[0]
                    text_x = (w - text_size[0]) // 2
                    text_y = (h + text_size[1]) // 2
                    
                    cv2.putText(display_frame, text, (text_x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 10)
                    cv2.putText(display_frame, text, (text_x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 120, 255), 5)
                    
                    cv2.imshow("Photobooth - Photo Strip!", display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        cap.release()
                        cv2.destroyAllWindows()
                        return []
        
        # Capture
        print("   📸 Smile!")
        ret, frame = cap.read()
        
        if ret:
            # Flash white!
            if not HEADLESS:
                try:
                    white_frame = frame.copy()
                    white_frame[:] = (255, 255, 255)
                    cv2.imshow("Photobooth - Photo Strip!", white_frame)
                    cv2.waitKey(150)  # Flash duration
                except:
                    pass
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strip_{timestamp}_{i+1}.jpg"
            filepath = os.path.join(PHOTOS_DIR, filename)
            cv2.imwrite(filepath, frame)
            photo_paths.append(filepath)
            print(f"   ✅ Captured!")
    
    cap.release()
    if not HEADLESS:
        cv2.destroyAllWindows()
    
    return photo_paths


def capture_photo_strip(camera_index=0, num_photos=3, countdown=3, width=1920, height=1080):
    """Capture multiple photos using the best available camera."""
    camera_type = detect_camera()
    
    if camera_type == 'picamera':
        return capture_photo_strip_picamera(num_photos, countdown, width, height)
    else:
        return capture_photo_strip_opencv(camera_index, num_photos, countdown, width, height)


def process_for_thermal(image_path):
    """
    Process an image for optimal thermal printer output.
    """
    from PIL import ImageEnhance, ImageFilter
    
    img = Image.open(image_path)
    
    # Resize to thermal printer width (576 pixels for 80mm paper)
    thermal_width = 576
    aspect_ratio = img.height / img.width
    new_height = int(thermal_width * aspect_ratio)
    img = img.resize((thermal_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Sharpening often increases noise/grain for dithered prints.
    # Instead, we slightly smooth to make the dithered dots clump better.
    img = img.filter(ImageFilter.SMOOTH)
    
    # Increase contrast for thermal printing
    # Reduced from 1.4 to 1.2 to prevent "blowing out" details before dithering
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    
    # Adjust brightness
    brightness = ImageEnhance.Brightness(img)
    img = brightness.enhance(1.1)
    
    # Convert to 1-bit with dithering
    img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    
    # Save processed image
    processed_path = image_path.replace('.jpg', '_thermal.png')
    img.save(processed_path)
    
    print(f"🖨️ Processed for thermal: {processed_path}")
    return processed_path


def print_photo(image_path):
    """Print a photo to the thermal printer."""
    print("🖨️ Connecting to printer...")
    
    try:
        printer = Usb(VENDOR_ID, PRODUCT_ID, 0)
        
        # Print header
        printer.set(align='center', bold=True, double_height=True, double_width=True)
        printer.text("THE OCHO\n")
        printer.set(align='center', bold=False, double_height=False, double_width=False)
        printer.text("PHOTOBOOTH\n")
        
        # Print timestamp (smaller)
        printer.set(align='center', font='b')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        printer.text(f"{timestamp}\n")
        printer.set(font='a')  # Reset font
        printer.text("\n")
        
        # Print the image
        print("🖨️ Printing image...")
        printer.image(image_path, impl="bitImageColumn")
        
        # Print footer
        printer.text("\n")
        printer.set(align='center')
        printer.text("Thanks for visiting!\n")
        printer.text("\n\n\n")  # Feed paper
        
        printer.cut()
        printer.close()
        
        print("✅ Print complete!")
        return True
        
    except Exception as e:
        print(f"❌ Print error: {e}")
        return False


def create_photo_strip(photo_paths, spacing=20):
    """Combine multiple photos into a vertical strip."""
    if not photo_paths:
        return None
    
    images = [Image.open(p) for p in photo_paths]
    
    # Resize all to same width
    target_width = 576
    resized = []
    for img in images:
        aspect = img.height / img.width
        new_height = int(target_width * aspect)
        resized.append(img.resize((target_width, new_height), Image.Resampling.LANCZOS))
    
    # Calculate total height
    total_height = sum(img.height for img in resized) + spacing * (len(resized) - 1)
    
    # Create strip
    strip = Image.new('RGB', (target_width, total_height), 'white')
    
    y_offset = 0
    for img in resized:
        strip.paste(img, (0, y_offset))
        y_offset += img.height + spacing
    
    # Save strip
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    strip_path = os.path.join(PHOTOS_DIR, f"photostrip_{timestamp}.jpg")
    strip.save(strip_path, quality=95)
    
    print(f"✅ Photo strip created: {strip_path}")
    return strip_path


def photobooth(camera_index=0, countdown=3, width=1920, height=1080):
    """Main photobooth function - capture and print a single photo."""
    print("\n" + "=" * 50)
    print("   📷 PHOTOBOOTH 📷")
    print("=" * 50 + "\n")
    
    # Step 1: Capture photo
    photo_path = capture_photo(camera_index, countdown, width, height)
    if not photo_path:
        print("❌ Photo capture failed")
        return False
    
    # Step 2: Process for thermal printing
    thermal_path = process_for_thermal(photo_path)
    
    # Step 3: Print!
    success = print_photo(thermal_path)
    
    if success:
        print("\n" + "=" * 50)
        print("   🎉 Photo printed! 🎉")
        print("=" * 50 + "\n")
    
    return success


def photobooth_strip(camera_index=0, countdown=3, num_photos=3, width=1920, height=1080):
    """Capture multiple photos, create a strip, and print it."""
    print("\n" + "=" * 50)
    print("   📷 PHOTOBOOTH - PHOTO STRIP MODE 📷")
    print(f"   Taking {num_photos} photos!")
    print("=" * 50 + "\n")
    
    # Step 1: Capture photos
    photo_paths = capture_photo_strip(camera_index, num_photos, countdown, width, height)
    if not photo_paths:
        print("❌ Photo capture failed")
        return False
    
    # Step 2: Create the strip
    strip_path = create_photo_strip(photo_paths)
    if not strip_path:
        print("❌ Failed to create strip")
        return False
    
    # Step 3: Process for thermal printing
    thermal_path = process_for_thermal(strip_path)
    
    # Step 4: Print!
    success = print_photo(thermal_path)
    
    if success:
        print("\n" + "=" * 50)
        print("   🎉 Photo strip printed! 🎉")
        print("=" * 50 + "\n")
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Photobooth - Capture and Print")
    parser.add_argument("--camera", "-c", type=int, default=0,
                        help="Camera index for OpenCV (default: 0)")
    parser.add_argument("--countdown", "-t", type=int, default=3,
                        help="Countdown seconds (default: 3, use 0 for instant)")
    parser.add_argument("--no-preview", action="store_true",
                        help="Skip preview window, capture instantly")
    parser.add_argument("--strip", "-s", action="store_true",
                        help="Photo strip mode: take 3 photos")
    parser.add_argument("--photos", "-n", type=int, default=3,
                        help="Number of photos for strip mode (default: 3)")
    parser.add_argument("--headless", action="store_true",
                        help="Run without GUI (for web server)")
    parser.add_argument("--picamera", action="store_true",
                        help="Force use of Pi Camera")
    parser.add_argument("--opencv", action="store_true",
                        help="Force use of OpenCV (USB webcam)")
    parser.add_argument("--width", type=int, default=1920,
                        help="Webcam width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080,
                        help="Webcam height (default: 1080)")
    
    args = parser.parse_args()
    
    # Set headless mode
    if args.headless:
        HEADLESS = True
    
    # Set camera type
    if args.picamera:
        CAMERA_TYPE = 'picamera'
    elif args.opencv:
        CAMERA_TYPE = 'opencv'
    
    countdown = 0 if args.no_preview else args.countdown
    
    if args.strip:
        photobooth_strip(camera_index=args.camera, countdown=countdown, num_photos=args.photos,
                        width=args.width, height=args.height)
    else:
        photobooth(camera_index=args.camera, countdown=countdown,
                  width=args.width, height=args.height)
