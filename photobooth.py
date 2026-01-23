"""
Photobooth - Capture and Print
Takes a photo from webcam and prints it on RONGTA thermal printer
"""

import os
import sys
import cv2
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


def capture_photo(camera_index=0, countdown=3):
    """
    Capture a photo from the webcam.
    
    Args:
        camera_index: Camera device index (0 for default webcam)
        countdown: Seconds to show preview before capture (0 for instant)
    
    Returns:
        Path to the captured image file, or None if failed
    """
    print("📷 Initializing camera...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("❌ Could not open camera")
        return None
    
    # Set higher resolution if supported
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("📷 Camera ready!")
    
    if countdown > 0:
        print(f"📷 Get ready! Taking photo in {countdown} seconds...")
        
        if HEADLESS:
            # Headless mode: just wait without GUI
            import time
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


def process_for_thermal(image_path, width=576):
    """
    Process an image for thermal printing.
    Resizes and converts to high-contrast black and white.
    
    Args:
        image_path: Path to the original image
        width: Width in pixels for thermal printer (576 for 80mm paper, 384 for 58mm)
    
    Returns:
        Path to the processed image
    """
    print("🔄 Processing image for thermal printer...")
    
    from PIL import ImageEnhance, ImageFilter
    
    # Open and resize
    img = Image.open(image_path)
    
    # Calculate new height maintaining aspect ratio
    aspect = img.height / img.width
    new_height = int(width * aspect)
    
    img = img.resize((width, new_height), Image.Resampling.LANCZOS)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Apply sharpening for clearer details
    img = img.filter(ImageFilter.SHARPEN)
    
    # Enhance contrast for better thermal print results
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.4)
    
    # Enhance brightness slightly
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)
    
    # Convert to 1-bit black and white using Floyd-Steinberg dithering
    img = img.convert('1')
    
    # Save processed image
    processed_path = image_path.replace('.jpg', '_thermal.png')
    img.save(processed_path)
    
    print(f"✅ Processed image saved: {processed_path}")
    return processed_path


def print_photo(image_path, title="THE OCHO PHOTOBOOTH"):
    """
    Print a photo to the thermal printer with a header.
    
    Args:
        image_path: Path to the image file
        title: Title to print above the photo
    """
    try:
        print("🖨️  Connecting to printer...")
        printer = Usb(VENDOR_ID, PRODUCT_ID)
        
        # Print header
        printer.set(align='center', bold=True, double_height=True, double_width=True)
        printer.text(f"\n{title}\n")
        
        printer.set(align='center', font='b', bold=False, double_height=False, double_width=False)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        printer.text(f"{timestamp}\n")
        printer.set(font='a')  # Reset to normal font
        printer.text("=" * 24 + "\n\n")
        
        # Print the image
        print("🖨️  Printing photo...")
        printer.image(image_path)
        
        # Print footer
        printer.text("\n")
        printer.text("-" * 24 + "\n")
        printer.set(align='center')
        printer.text("Thanks for visiting!\n")
        printer.text("\n\n\n")
        
        # Cut paper if supported
        try:
            printer.cut()
        except:
            pass
        
        printer.close()
        print("✅ Photo printed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error printing: {e}")
        return False


def photobooth(camera_index=0, countdown=3):
    """
    Main photobooth function - captures and prints a photo.
    
    Args:
        camera_index: Camera device index
        countdown: Seconds for countdown (0 for instant capture)
    """
    print("\n" + "=" * 50)
    print("   📷 PHOTOBOOTH 📷")
    print("=" * 50 + "\n")
    
    # Step 1: Capture photo
    photo_path = capture_photo(camera_index, countdown)
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


def capture_photo_strip(camera_index=0, num_photos=3, countdown=3):
    """
    Capture multiple photos for a photo strip.
    
    Args:
        camera_index: Camera device index
        num_photos: Number of photos to take
        countdown: Seconds between each photo
    
    Returns:
        List of paths to captured images
    """
    print(f"📷 Photo strip mode: Taking {num_photos} photos!")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return []
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    photo_paths = []
    
    for i in range(num_photos):
        print(f"\n📸 Photo {i + 1} of {num_photos}")
        
        if countdown > 0:
            print(f"   Get ready in {countdown}...")
            
            if HEADLESS:
                # Headless mode: just wait without GUI
                import time
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


def create_photo_strip(photo_paths, spacing=20):
    """
    Combine multiple photos into a vertical strip.
    
    Args:
        photo_paths: List of paths to photos
        spacing: Pixels between photos
    
    Returns:
        Path to the combined strip image
    """
    print("🔄 Creating photo strip...")
    
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
    strip.save(strip_path)
    
    print(f"✅ Strip saved: {strip_path}")
    return strip_path


def photobooth_strip(camera_index=0, countdown=3, num_photos=3):
    """
    Photo strip mode - captures multiple photos and prints them as a strip.
    
    Args:
        camera_index: Camera device index
        countdown: Seconds between photos
        num_photos: Number of photos to take
    """
    print("\n" + "=" * 50)
    print("   📷 PHOTO STRIP MODE 📷")
    print("=" * 50 + "\n")
    
    # Step 1: Capture multiple photos
    photo_paths = capture_photo_strip(camera_index, num_photos, countdown)
    if not photo_paths:
        print("❌ Photo capture failed")
        return False
    
    # Step 2: Create strip
    strip_path = create_photo_strip(photo_paths)
    
    # Step 3: Process for thermal
    thermal_path = process_for_thermal(strip_path)
    
    # Step 4: Print!
    success = print_photo(thermal_path, title="THE OCHO PHOTO STRIP")
    
    if success:
        print("\n" + "=" * 50)
        print("   🎉 Photo strip printed! 🎉")
        print("=" * 50 + "\n")
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Photobooth - Capture and Print")
    parser.add_argument("--camera", "-c", type=int, default=0,
                        help="Camera index (default: 0)")
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
    
    args = parser.parse_args()
    
    # Set headless mode
    if args.headless:
        HEADLESS = True
    
    countdown = 0 if args.no_preview else args.countdown
    
    if args.strip:
        photobooth_strip(camera_index=args.camera, countdown=countdown, num_photos=args.photos)
    else:
        photobooth(camera_index=args.camera, countdown=countdown)


