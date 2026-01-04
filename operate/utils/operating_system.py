"""OS control utilities"""
import pyautogui
import time
from loguru import logger
from operate.utils.misc import convert_percent_to_decimal

class OperatingSystem:
    def write(self, content):
        logger.info("Typing text")
        if not content:
            return
        try:
            content = content.replace("\\n", "\n")
            for char in content:
                pyautogui.write(char)
        except Exception as e:
            logger.error(f"Write failed: {e}")

    def press(self, keys):
        logger.info(f"Pressing: {keys}")
        if not keys:
            return
        try:
            # Use hotkey for multiple keys
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys[0])
        except Exception as e:
            logger.error(f"Press failed: {e}")

    def mouse(self, click_detail):
        logger.info("Mouse click")
        if not click_detail:
            logger.warning("No click details")
            return
        try:
            x = convert_percent_to_decimal(click_detail.get("x"))
            y = convert_percent_to_decimal(click_detail.get("y"))
            if x is not None and y is not None:
                self.click_at_percentage(x, y)
            else:
                logger.warning(f"Invalid coords: {click_detail}")
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
            logger.debug(f"Clicked at ({x}, {y})")
        except Exception as e:
            logger.error(f"Click failed: {e}")

    def scroll(self, amount=-10):
        logger.info("Scrolling")
        try:
            pyautogui.scroll(amount)
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
