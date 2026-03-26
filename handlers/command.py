"""Command Handlers - Execute structured commands"""
import subprocess
import platform
import time
import os
from typing import Dict, Any, Optional
from core.models import CommandType

class CommandHandler:
    """Execute structured commands safely"""
    
    @staticmethod
    def execute(command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command and return result"""
        try:
            if command_type == CommandType.PRESS.value:
                return CommandHandler.press_keys(params)
            elif command_type == CommandType.CLICK.value:
                return CommandHandler.click(params)
            elif command_type == CommandType.WRITE.value:
                return CommandHandler.write_text(params)
            elif command_type == CommandType.SCREENSHOT.value:
                return CommandHandler.screenshot(params)
            elif command_type == CommandType.SYSTEM_INFO.value:
                return CommandHandler.system_info(params)
            elif command_type == CommandType.SLEEP.value:
                return CommandHandler.sleep_cmd(params)
            elif command_type == CommandType.OPEN_APP.value:
                return CommandHandler.open_app(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command type: {command_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def press_keys(params: Dict[str, Any]) -> Dict[str, Any]:
        """Press keyboard keys"""
        try:
            import pyautogui
            keys = params.get("keys", [])
            if not keys:
                return {"success": False, "error": "No keys specified"}
            
            pyautogui.hotkey(*keys)
            return {
                "success": True,
                "action": "press",
                "keys": keys
            }
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def click(params: Dict[str, Any]) -> Dict[str, Any]:
        """Click at coordinates"""
        try:
            import pyautogui
            x = params.get("x", 0.5)
            y = params.get("y", 0.5)
            
            # If percentages, convert to pixels
            if isinstance(x, (int, float)) and x <= 1:
                w, h = pyautogui.size()
                x, y = int(w * x), int(h * y)
            
            pyautogui.click(int(x), int(y))
            return {
                "success": True,
                "action": "click",
                "position": {"x": x, "y": y}
            }
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def write_text(params: Dict[str, Any]) -> Dict[str, Any]:
        """Write text"""
        try:
            import pyautogui
            text = params.get("text", "")
            interval = params.get("interval", 0.05)
            
            pyautogui.write(text, interval=interval)
            return {
                "success": True,
                "action": "write",
                "text": text
            }
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def screenshot(params: Dict[str, Any]) -> Dict[str, Any]:
        """Capture screenshot"""
        try:
            import pyautogui
            import base64
            from io import BytesIO
            from PIL import Image
            
            img = pyautogui.screenshot()
            buf = BytesIO()
            img.save(buf, format='PNG')
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "action": "screenshot",
                "image": img_b64[:100] + "..." if len(img_b64) > 100 else img_b64
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
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def sleep_cmd(params: Dict[str, Any]) -> Dict[str, Any]:
        """Sleep for specified seconds"""
        try:
            seconds = params.get("seconds", 1)
            time.sleep(seconds)
            return {
                "success": True,
                "action": "sleep",
                "seconds": seconds
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def open_app(params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application"""
        try:
            app = params.get("app", "")
            if not app:
                return {"success": False, "error": "No app specified"}
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", app])
            elif system == "Windows":
                subprocess.Popen([app])
            else:  # Linux
                subprocess.Popen([app])
            
            time.sleep(1)  # Give app time to start
            
            return {
                "success": True,
                "action": "open_app",
                "app": app
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
