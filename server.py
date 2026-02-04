"""
Photobooth Web Server
Provides a web interface to trigger the photobooth from a phone
"""

import os
import sys
import threading
import json
import hmac
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from photobooth import PhotoboothCamera, process_for_thermal, print_photo, create_photo_strip
import glob

# Set library path for libusb on macOS
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

# Get paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(SCRIPT_DIR, "photos")
FRONTEND_DIR = os.path.join(SCRIPT_DIR, "frontend", "dist")


app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("PHOTOBOOTH_SECURE_COOKIES", "false").lower() == "true"
)

session_secret = os.environ.get("PHOTOBOOTH_SESSION_SECRET")
if session_secret:
    app.secret_key = session_secret
else:
    # Keeps sessions working in development when no secret is configured.
    # Set PHOTOBOOTH_SESSION_SECRET in production to persist sessions across restarts.
    app.secret_key = os.urandom(32)
    print("⚠️  PHOTOBOOTH_SESSION_SECRET is not set. Using a temporary secret.")

API_PASSWORD = os.environ.get("PHOTOBOOTH_API_PASSWORD", "photobooth")
if API_PASSWORD == "photobooth":
    print("⚠️  Using default API password. Set PHOTOBOOTH_API_PASSWORD to secure access.")

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


# Metadata file path
METADATA_FILE = os.path.join(PHOTOS_DIR, "metadata.json")
photo_metadata = {}

def load_metadata():
    global photo_metadata
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                photo_metadata = json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            photo_metadata = {}

def save_metadata():
    try:
        with open(METADATA_FILE, 'w') as f:
            json.dump(photo_metadata, f)
    except Exception as e:
        print(f"Error saving metadata: {e}")

# Load metadata on startup
load_metadata()


PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/auth/status",
}


def is_api_authenticated():
    return session.get("api_authenticated") is True


@app.before_request
def require_api_authentication():
    """Require an authenticated session for API routes."""
    if not request.path.startswith("/api/"):
        return None

    if request.method == "OPTIONS":
        return None

    if request.path in PUBLIC_API_PATHS:
        return None

    if is_api_authenticated():
        return None

    return jsonify({"status": "error", "message": "Authentication required"}), 401


@app.route('/api/auth/status')
def auth_status():
    """Check whether the current session is authenticated."""
    return jsonify({"authenticated": is_api_authenticated()})


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Start an authenticated session using the configured API password."""
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))

    if not hmac.compare_digest(password, API_PASSWORD):
        session.pop("api_authenticated", None)
        return jsonify({"status": "error", "message": "Invalid password"}), 401

    session["api_authenticated"] = True
    return jsonify({"status": "success"})


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """End the current authenticated session."""
    session.pop("api_authenticated", None)
    return jsonify({"status": "success"})




def get_sorted_photos():
    """Get all photos sorted by newest first with metadata"""
    # pattern match both jpg and png
    files = glob.glob(os.path.join(PHOTOS_DIR, "*.jpg"))
    
    photo_list = []
    for f in files:
        filename = os.path.basename(f)
        if filename.startswith("strip_"):
            # Strip source shots are internal; only show final outputs in gallery.
            continue
        timestamp = os.path.getmtime(f)
        is_liked = photo_metadata.get(filename, {}).get("liked", False)
        
        photo_list.append({
            "filename": filename,
            "timestamp": timestamp,
            "liked": is_liked
        })

    # Sort by modification time, newest first (default)
    photo_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return photo_list


@app.route('/')
def index():
    """Serve the React app"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/gallery')
def gallery():
    """Serve the React app (SPA routing)"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/status')
def status():
    """Get current status"""
    return jsonify({
        "in_progress": photo_in_progress,
        **last_result
    })


@app.route('/api/photos')
def list_photos():
    """Get list of all photos with metadata"""
    photos = get_sorted_photos()
    return jsonify({"photos": photos})


@app.route('/api/like/<path:filename>', methods=['POST'])
def toggle_like(filename):
    """Toggle the liked status of a photo"""
    filename = os.path.basename(filename)
    
    if filename not in photo_metadata:
        photo_metadata[filename] = {}
        
    current_status = photo_metadata[filename].get("liked", False)
    photo_metadata[filename]["liked"] = not current_status
    
    save_metadata()
    
    return jsonify({
        "status": "success", 
        "filename": filename, 
        "liked": photo_metadata[filename]["liked"]
    })


@app.route('/api/reprint/<path:filename>', methods=['POST'])
def reprint_photo(filename):
    """Reprint a specific photo"""
    try:
        # Sanitize filename (basic check)
        filename = os.path.basename(filename)
        filepath = os.path.join(PHOTOS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "File not found"}), 404
            
        def do_print():
            # Check for existing thermal version or process unique 
            # (Photobooth.process_for_thermal handles creating the file)
            # Determine if it's a strip based on filename or just try generic?
            # Our filenames: "photo_..." or "photostrip_..."
            is_strip = "photostrip" in filename
            thermal_path = process_for_thermal(filepath, is_strip=is_strip)
            print_photo(thermal_path)
            
        # Run in background to not block
        thread = threading.Thread(target=do_print)
        thread.start()
        
        return jsonify({"status": "success", "message": "Reprinting..."})
        
    except Exception as e:
        print(f"Error reprinting: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/delete/<path:filename>', methods=['POST'])
def delete_photo(filename):
    """Delete a photo and its associated data"""
    try:
        filename = os.path.basename(filename)
        filepath = os.path.join(PHOTOS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "File not found"}), 404
            
        # Delete original file
        os.remove(filepath)
        
        # Delete thermal version if exists
        thermal_path = filepath.replace('.jpg', '_thermal.png')
        if os.path.exists(thermal_path):
            os.remove(thermal_path)
            
        # Remove from metadata
        if filename in photo_metadata:
            del photo_metadata[filename]
            save_metadata()
            
        return jsonify({"status": "success", "message": "Photo deleted"})
        
    except Exception as e:
        print(f"Error deleting photo: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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


import time

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
        
        try:
            photo_paths = []
            num_photos = 3
            
            for i in range(num_photos):
                # 1. Countdown Phase
                target_time = time.time() + 3  # 3 seconds from now
                last_result = {
                    "status": "countdown", 
                    "target_timestamp": target_time,
                    "photo_index": i + 1,
                    "total_photos": num_photos,
                    "message": f"Pose {i+1}/{num_photos}"
                }
                
                # Sleep until target time (approx)
                time.sleep(3)
                
                # 2. Capture Phase
                last_result = {
                    "status": "capturing", 
                    "message": "SNAP!"
                }
                
                # Capture immediately (countdown=0 because we handled it)
                path = camera.capture(countdown=0)
                if path:
                    photo_paths.append(path)
                
                # 3. Gap Phase (if not last photo)
                if i < num_photos - 1:
                    target_time = time.time() + 2  # 2 seconds gap
                    last_result = {
                        "status": "waiting",
                        "target_timestamp": target_time,
                        "message": "Next pose..."
                    }
                    time.sleep(2)

            # Process strip
            if photo_paths:
                last_result = {"status": "processing", "message": "Stitching strip..."}
                strip_path = create_photo_strip(photo_paths)
                
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
    response = send_from_directory(PHOTOS_DIR, filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response





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
