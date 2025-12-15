"""Screenshot utilities"""
import subprocess
import base64
import io
from PIL import Image, ImageDraw
from loguru import logger

def capture_screenshot():
    path = "/tmp/screenshot.png"

    for cmd in [f"grim {path}", f"scrot {path}", f"gnome-screenshot -f {path}"]:
        try:
            if subprocess.run(cmd, shell=True, capture_output=True).returncode == 0:
                return Image.open(path)
        except: pass

    raise Exception("No screenshot tool found")

def capture_screen_with_cursor(output_path):
    img = capture_screenshot()

    try:
        import pyautogui
        x, y = pyautogui.position()
        draw = ImageDraw.Draw(img)
        draw.ellipse([x-10, y-10, x+10, y+10], outline="red", width=3)
    except Exception as e:
        logger.debug(f"No cursor: {e}")

    img.save(output_path)
    return output_path

def get_screenshot_base64():
    """Get screenshot as base64"""
    img = capture_screenshot()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')
