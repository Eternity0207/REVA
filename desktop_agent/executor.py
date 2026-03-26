"""Command executor for REVA desktop app"""
import logging
import time
import platform
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Execute commands locally"""
    
    @staticmethod
    def execute(command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command"""
        try:
            if command_type == "press":
                return CommandExecutor.press_keys(params)
            elif command_type == "click":
                return CommandExecutor.click(params)
            elif command_type == "write":
                return CommandExecutor.write_text(params)
            elif command_type == "screenshot":
                return CommandExecutor.screenshot(params)
            elif command_type == "system_info":
                return CommandExecutor.system_info(params)
            elif command_type == "sleep":
                return CommandExecutor.sleep_cmd(params)
            elif command_type == "open_app":
                return CommandExecutor.open_app(params)
            else:
                return {"success": False, "error": f"Unknown command: {command_type}"}
        except Exception as e:
            logger.error(f"Execute error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def press_keys(params: Dict[str, Any]) -> Dict[str, Any]:
        """Press keyboard keys"""
        try:
            import pyautogui
            keys = params.get("keys", [])
            if not keys:
                return {"success": False, "error": "No keys specified"}
            
            pyautogui.hotkey(*keys)
            logger.info(f"Pressed keys: {keys}")
            return {
                "success": True,
                "action": "press",
                "keys": keys
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def click(params: Dict[str, Any]) -> Dict[str, Any]:
        """Click mouse"""
        try:
            import pyautogui
            x = params.get("x", 0)
            y = params.get("y", 0)
            
            pyautogui.click(x, y)
            logger.info(f"Clicked at ({x}, {y})")
            return {
                "success": True,
                "action": "click",
                "x": x,
                "y": y
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def write_text(params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text"""
        try:
            import pyautogui
            text = params.get("text", "")
            
            pyautogui.write(text)
            logger.info(f"Typed: {text}")
            return {
                "success": True,
                "action": "write",
                "text": text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def screenshot(params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot"""
        try:
            import pyautogui
            import base64
            import io
            
            img = pyautogui.screenshot()
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info("Screenshot taken")
            return {
                "success": True,
                "action": "screenshot",
                "image_base64": b64,
                "width": img.width,
                "height": img.height
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def system_info(params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "success": True,
                "action": "system_info",
                "os": platform.system(),
                "platform": platform.platform(),
                "hostname": os.getenv("HOSTNAME", "unknown"),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def sleep_cmd(params: Dict[str, Any]) -> Dict[str, Any]:
        """Sleep for N seconds"""
        try:
            seconds = params.get("seconds", 1)
            time.sleep(seconds)
            logger.info(f"Slept for {seconds}s")
            return {
                "success": True,
                "action": "sleep",
                "seconds": seconds
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def open_app(params: Dict[str, Any]) -> Dict[str, Any]:
        """Open application"""
        try:
            import subprocess
            app = params.get("app", "")
            if not app:
                return {"success": False, "error": "No app specified"}
            
            if platform.system() == "Windows":
                subprocess.Popen(app)
            elif platform.system() == "Darwin":  # Mac
                subprocess.Popen(["open", "-a", app])
            else:  # Linux
                subprocess.Popen([app])
            
            logger.info(f"Opened app: {app}")
            return {
                "success": True,
                "action": "open_app",
                "app": app
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
