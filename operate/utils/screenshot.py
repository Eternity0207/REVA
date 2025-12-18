"""Screenshot utilities"""
import subprocess
import base64
import io
import os
from PIL import Image, ImageDraw
from loguru import logger

def capture_screenshot():
    path = "/tmp/screenshot.png"

    commands = [
        f"grim {path}",
        f"scrot {path}",
        f"gnome-screenshot -f {path}"
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode == 0 and os.path.exists(path):
                return Image.open(path)
        except Exception as e:
            logger.debug(f"Failed: {cmd} - {e}")

    raise Exception("Screenshot capture failed")

def capture_screen_with_cursor(output_path):
    try:
        img = capture_screenshot()

        try:
            import pyautogui
            x, y = pyautogui.position()
            draw = ImageDraw.Draw(img)
            draw.ellipse([x-10, y-10, x+10, y+10], outline="red", width=3)
        except:
            pass

        img.save(output_path)
        return output_path
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise

def get_screenshot_base64():
    img = capture_screenshot()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')
