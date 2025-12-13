"""Screenshot utilities"""
import subprocess
import platform
from PIL import Image, ImageDraw
from loguru import logger

def capture_screenshot():
    path = "/tmp/screenshot.png"
    system = platform.system()

    if system == "Linux":
        for cmd in [f"grim {path}", f"scrot {path}", f"gnome-screenshot -f {path}"]:
            try:
                if subprocess.run(cmd, shell=True, capture_output=True).returncode == 0:
                    return Image.open(path)
            except: pass
    elif system == "Darwin":  # macOS
        try:
            subprocess.run(f"screencapture -x {path}", shell=True, capture_output=True)
            return Image.open(path)
        except: pass
    elif system == "Windows":
        try:
            import pyautogui
            img = pyautogui.screenshot()
            img.save(path)
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
