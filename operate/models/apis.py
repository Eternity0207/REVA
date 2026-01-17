"""LLM API integrations"""
import os
import json
import base64
from loguru import logger
from operate.config import Config
from operate.exceptions import ModelNotRecognizedException
from operate.utils.screenshot import capture_screen_with_cursor
from operate.models.prompts import get_user_prompt, get_user_first_message_prompt

config = Config()

GROQ_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def clean_json(content):
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return content.strip()

def get_screenshot_base64():
    """Capture and encode screenshot"""
    os.makedirs("screenshots", exist_ok=True)
    path = "screenshots/screenshot.png"
    capture_screen_with_cursor(path)

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), path
