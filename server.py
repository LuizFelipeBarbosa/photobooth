"""
Photobooth Web Server
Provides a web interface to trigger the photobooth from a phone
"""

import os
import sys
import subprocess
import threading
import time
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS

# Set library path for libusb on macOS
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")

# Get paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(SCRIPT_DIR, "photos")
VENV_PYTHON = os.path.join(SCRIPT_DIR, "venv", "bin", "python")

# Use system python if venv doesn't exist
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Track if a photo is currently being taken
photo_in_progress = False
last_result = {"status": "ready", "message": "Ready to take photos!"}


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
    """Take a single photo"""
    global photo_in_progress, last_result
    
    if photo_in_progress:
        return jsonify({"status": "error", "message": "Photo already in progress!"}), 400
    
    def capture():
        global photo_in_progress, last_result
        photo_in_progress = True
        last_result = {"status": "capturing", "message": "Say cheese! 📸"}
        
        try:
            # Run photobooth as subprocess
            result = subprocess.run(
                [VENV_PYTHON, "photobooth.py", "--headless", "--countdown", "3"],
                cwd=SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                last_result = {"status": "success", "message": "Photo printed! 🎉"}
            else:
                error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Capture failed"
                last_result = {"status": "error", "message": error_msg[:100]}
        except subprocess.TimeoutExpired:
            last_result = {"status": "error", "message": "Photo capture timed out"}
        except Exception as e:
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
    
    def capture():
        global photo_in_progress, last_result
        photo_in_progress = True
        last_result = {"status": "capturing", "message": "Photo strip mode! 📸📸📸"}
        
        try:
            # Run photobooth as subprocess
            result = subprocess.run(
                [VENV_PYTHON, "photobooth.py", "--headless", "--strip", "--countdown", "3"],
                cwd=SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                last_result = {"status": "success", "message": "Photo strip printed! 🎉"}
            else:
                error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Capture failed"
                last_result = {"status": "error", "message": error_msg[:100]}
        except subprocess.TimeoutExpired:
            last_result = {"status": "error", "message": "Photo capture timed out"}
        except Exception as e:
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
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
