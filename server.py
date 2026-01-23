"""
Photobooth Web Server
Provides a web interface to trigger the photobooth from a phone
"""

import os
import sys
import threading
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from photobooth import PhotoboothCamera, process_for_thermal, print_photo, create_photo_strip

# Set library path for libusb on macOS
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

# Get paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(SCRIPT_DIR, "photos")

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Global Camera Instance
camera = None

# Track if a photo is currently being taken
photo_in_progress = False
last_result = {"status": "ready", "message": "Ready to take photos!"}


def init_camera():
    global camera
    if camera is None:
        try:
            # Headless = True because this is a web server
            camera = PhotoboothCamera(headless=True)
            print("✅ Global camera initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize camera: {e}")

# Initialize camera on startup
init_camera()


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Get current status"""
    return jsonify({
        "in_progress": photo_in_progress,
        **last_result
    })


@app.route('/api/photo', methods=['POST'])
def take_photo():
    """Take a single photo using the persistent camera"""
    global photo_in_progress, last_result
    
    if photo_in_progress:
        return jsonify({"status": "error", "message": "Photo already in progress!"}), 400
    
    if not camera:
        return jsonify({"status": "error", "message": "Camera not initialized!"}), 500
    
    def capture():
        global photo_in_progress, last_result
        photo_in_progress = True
        last_result = {"status": "capturing", "message": "Say cheese! 📸"}
        
        try:
            # Pass countdown=3 to let the backend sleep and sync with frontend
            filepath = camera.capture(countdown=3)
            
            if filepath:
                filename = os.path.basename(filepath)
                last_result = {
                    "status": "success", 
                    "message": "Photo captured! Printing...", 
                    "photo_url": f"/photos/{filename}"
                }
                
                # Print in background (don't block the "success" display strictly, 
                # but usually we want to print before saying done? 
                # Ideally, we return the photo URL immediately for display, 
                # then print asynchronously.
                # But 'photobooth.py' logic was capture -> process -> print.
                
                thermal_path = process_for_thermal(filepath)
                print_photo(thermal_path)
                
            else:
                last_result = {"status": "error", "message": "Capture returned empty"}
        except Exception as e:
            print(f"Error taking photo: {e}")
            last_result = {"status": "error", "message": str(e)[:100]}
        finally:
            photo_in_progress = False
    
    thread = threading.Thread(target=capture)
    thread.start()
    
    return jsonify({"status": "started", "message": "Taking photo..."})


@app.route('/api/strip', methods=['POST'])
def take_strip():
    """Take a photo strip (3 photos)"""
    global photo_in_progress, last_result
    
    if photo_in_progress:
        return jsonify({"status": "error", "message": "Photo already in progress!"}), 400
    
    if not camera:
        return jsonify({"status": "error", "message": "Camera not initialized!"}), 500
    
    def capture():
        global photo_in_progress, last_result
        photo_in_progress = True
        last_result = {"status": "capturing", "message": "Photo strip mode! 📸📸📸"}
        
        try:
            paths = camera.capture_strip(num_photos=3, countdown=3)
            
            if paths:
                strip_path = create_photo_strip(paths)
                
                if strip_path:
                    filename = os.path.basename(strip_path)
                    last_result = {
                        "status": "success", 
                        "message": "Strip captured! Printing...",
                        "photo_url": f"/photos/{filename}"
                    }
                    
                    thermal_path = process_for_thermal(strip_path, is_strip=True)
                    print_photo(thermal_path)
                else:
                    last_result = {"status": "error", "message": "Failed to stitch strip"}
            else:
                last_result = {"status": "error", "message": "Failed to capture strip photos"}
                
        except Exception as e:
            print(f"Error taking strip: {e}")
            last_result = {"status": "error", "message": str(e)[:100]}
        finally:
            photo_in_progress = False
    
    thread = threading.Thread(target=capture)
    thread.start()
    
    return jsonify({"status": "started", "message": "Taking photo strip..."})


@app.route('/photos/<path:filename>')
def serve_photo(filename):
    """Serve photos from the photos directory"""
    return send_from_directory(PHOTOS_DIR, filename)


if __name__ == '__main__':
    # Get local IP for phone access
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    print("\n" + "=" * 50)
    print("   📷 PHOTOBOOTH WEB SERVER 📷")
    print("=" * 50)
    print(f"\n   Local:   http://localhost:8080")
    print(f"   Network: http://{local_ip}:8080")
    print("\n   Open the Network URL on your phone!")
    print("=" * 50 + "\n")
    
    # We don't want to reloader to restart and kill the camera constantly
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
