"""Screenshot utilities"""
import subprocess
from PIL import Image

def capture_screenshot():
    """Capture screen using available tools"""
    path = "/tmp/screenshot.png"

    # Try grim (Wayland)
    result = subprocess.run(f"grim {path}", shell=True, capture_output=True)
    if result.returncode == 0:
        return Image.open(path)

    # Try scrot (X11)
    result = subprocess.run(f"scrot {path}", shell=True, capture_output=True)
    if result.returncode == 0:
        return Image.open(path)

    raise Exception("No screenshot tool found")
