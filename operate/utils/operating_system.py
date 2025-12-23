"""OS control utilities"""
import pyautogui
from loguru import logger

class OperatingSystem:
    def write(self, content):
        """Type text"""
        logger.info("Typing text")
        try:
            for char in content:
                pyautogui.write(char)
        except Exception as e:
            logger.error(f"Write failed: {e}")

    def press(self, keys):
        """Press keys"""
        logger.info(f"Pressing: {keys}")
        try:
            for k in keys:
                pyautogui.keyDown(k)
            for k in keys:
                pyautogui.keyUp(k)
        except Exception as e:
            logger.error(f"Press failed: {e}")
