import subprocess
from PIL import Image, ImageDraw
import os
from loguru import logger


def capture_screenshot():
    """Capture screenshot with fallback methods"""
    screenshot_path = "/tmp/screenshot.png"

    # Try grim (Wayland)
    try:
        result = subprocess.run("grim " + screenshot_path, shell=True, capture_output=True)
        if result.returncode == 0:
            return Image.open(screenshot_path)
    except:
        pass

    # Try scrot (X11)
    try:
        result = subprocess.run("scrot " + screenshot_path, shell=True, capture_output=True)
        if result.returncode == 0:
            return Image.open(screenshot_path)
    except:
        pass

    # Try gnome-screenshot
    try:
        result = subprocess.run(f"gnome-screenshot -f {screenshot_path}", shell=True, capture_output=True)
        if result.returncode == 0:
            return Image.open(screenshot_path)
    except:
        pass

    raise Exception("Failed to capture screenshot - no supported screenshot tool found")


def capture_screen_with_cursor(output_path):
    """
    Capture screenshot and save to specified path.
    Adds cursor position indicator if possible.
    """
    try:
        # Capture the screenshot
        img = capture_screenshot()

        # Try to get cursor position and draw indicator
        try:
            import pyautogui
            cursor_x, cursor_y = pyautogui.position()

            # Draw a small circle at cursor position
            draw = ImageDraw.Draw(img)
            radius = 10
            draw.ellipse(
                [cursor_x - radius, cursor_y - radius, cursor_x + radius, cursor_y + radius],
                outline="red",
                width=3
            )
        except Exception as e:
            logger.debug(f"Could not add cursor indicator: {e}")

        # Save the image
        img.save(output_path)
        logger.debug(f"Screenshot saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to capture screen: {e}")
        raise


def get_screenshot_bytes():
    """Get screenshot as bytes"""
    import io
    img = capture_screenshot()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def get_screenshot_base64():
    """Get screenshot as base64 encoded string"""
    import base64
    screenshot_bytes = get_screenshot_bytes()
    return base64.b64encode(screenshot_bytes).decode('utf-8')
