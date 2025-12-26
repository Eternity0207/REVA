"""OS control utilities"""
import pyautogui
import time
from loguru import logger
from operate.utils.misc import convert_percent_to_decimal

class OperatingSystem:
    def write(self, content):
        logger.info("Typing text")
        try:
            content = content.replace("\\n", "\n")
            for char in content:
                pyautogui.write(char)
        except Exception as e:
            logger.error(f"Write failed: {e}")

    def press(self, keys):
        logger.info(f"Pressing: {keys}")
        try:
            for k in keys:
                pyautogui.keyDown(k)
            time.sleep(0.1)
            for k in keys:
                pyautogui.keyUp(k)
        except Exception as e:
            logger.error(f"Press failed: {e}")

    def mouse(self, click_detail):
        logger.info("Mouse click")
        try:
            x = convert_percent_to_decimal(click_detail.get("x"))
            y = convert_percent_to_decimal(click_detail.get("y"))
            if x and y:
                self.click_at_percentage(x, y)
        except Exception as e:
            logger.error(f"Click failed: {e}")

    def click_at_percentage(self, x_pct, y_pct, duration=0.8):
        try:
            if x_pct <= 1:
                w, h = pyautogui.size()
                x, y = int(w * x_pct), int(h * y_pct)
            else:
                x, y = int(x_pct), int(y_pct)

            pyautogui.moveTo(x, y, duration)
            pyautogui.click(x, y)
        except Exception as e:
            logger.error(f"Click failed: {e}")
