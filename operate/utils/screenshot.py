"""Screenshot utilities"""
import subprocess
from PIL import Image
from loguru import logger

def capture_screenshot():
    """Capture screen using available tools"""
    path = "/tmp/screenshot.png"

    # Try grim (Wayland)
    try:
        result = subprocess.run(f"grim {path}", shell=True, capture_output=True)
        if result.returncode == 0:
            return Image.open(path)
    except: pass

    # Try scrot (X11)
    try:
        result = subprocess.run(f"scrot {path}", shell=True, capture_output=True)
        if result.returncode == 0:
            return Image.open(path)
    except: pass

    # Try gnome-screenshot
    try:
        result = subprocess.run(f"gnome-screenshot -f {path}", shell=True, capture_output=True)
        if result.returncode == 0:
            return Image.open(path)
    except: pass

    raise Exception("No screenshot tool found")
