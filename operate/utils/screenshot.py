"""Screenshot utilities"""
import subprocess
import base64
import io
from PIL import Image, ImageDraw
from loguru import logger

MAX_SIZE = (1920, 1080)

def capture_screenshot():
    path = "/tmp/screenshot.png"

    for cmd in [f"grim {path}", f"scrot {path}", f"gnome-screenshot -f {path}"]:
        try:
            if subprocess.run(cmd, shell=True, capture_output=True).returncode == 0:
                return Image.open(path)
        except: pass

    raise Exception("No screenshot tool found")

def resize_if_needed(img):
    if img.size[0] > MAX_SIZE[0] or img.size[1] > MAX_SIZE[1]:
        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
    return img

def capture_screen_with_cursor(output_path):
    img = capture_screenshot()
    img = resize_if_needed(img)

    try:
        import pyautogui
        x, y = pyautogui.position()
        scale_x = img.size[0] / pyautogui.size()[0]
        scale_y = img.size[1] / pyautogui.size()[1]
        draw = ImageDraw.Draw(img)
        draw.ellipse([x*scale_x-10, y*scale_y-10, x*scale_x+10, y*scale_y+10], outline="red", width=3)
    except Exception as e:
        logger.debug(f"No cursor: {e}")

    img.save(output_path)
    return output_path

def get_screenshot_base64():
    img = capture_screenshot()
    img = resize_if_needed(img)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')
