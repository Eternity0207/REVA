import base64
import io
import json
import os
import time

from PIL import Image
from loguru import logger
import requests

from operate.config import Config
from operate.exceptions import ModelNotRecognizedException
from operate.models.prompts import (
    get_system_prompt,
    get_user_first_message_prompt,
    get_user_prompt,
    get_som_prompt
)
from operate.utils.screenshot import capture_screenshot, capture_screen_with_cursor
from operate.utils.style import ANSI_BRIGHT_MAGENTA, ANSI_GREEN, ANSI_RED, ANSI_RESET

# Load configuration
config = Config()

# OmniParser server URL (runs separately)
OMNIPARSER_URL = os.getenv("OMNIPARSER_URL", "http://localhost:8001")

# Groq vision model
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")


def clean_json(content):
    """Clean JSON response from LLM"""
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def get_screenshot_base64():
    """Capture screenshot and return as base64"""
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
    capture_screen_with_cursor(screenshot_filename)

    with open(screenshot_filename, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    return img_base64, screenshot_filename


def add_labels(screenshot_path):
    """Add labels to screenshot using OmniParser or local processing"""
    try:
        # Try OmniParser server first
        with open(screenshot_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        response = requests.post(
            f"{OMNIPARSER_URL}/label/",
            json={"base64_image": img_base64},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            labeled_path = screenshot_path.replace(".png", "_labeled.png")

            # Decode and save labeled image
            if "labeled_image" in result:
                img_data = base64.b64decode(result["labeled_image"])
                with open(labeled_path, "wb") as f:
                    f.write(img_data)

            return labeled_path, result.get("parsed_content_list", [])

    except Exception as e:
        logger.warning(f"OmniParser not available: {e}")

    # Fallback: return original image with empty labels
    return screenshot_path, []


def get_label_coordinates(label_id, content_list):
    """Get coordinates for a labeled element"""
    for item in content_list:
        if item.get("label") == label_id:
            bbox = item.get("bbox", [0, 0, 0, 0])
            # Return center of bounding box
            x = (bbox[0] + bbox[2]) / 2
            y = (bbox[1] + bbox[3]) / 2
            return x, y
    return None, None


def get_click_position_in_percent(label_id, content_list):
    """Get click position as percentage of screen"""
    x, y = get_label_coordinates(label_id, content_list)
    if x is not None and y is not None:
        return {"x": x, "y": y}
    return None


async def get_next_action(model, messages, objective, session_id):
    """
    Get next action from LLM based on current screen state.

    Parameters:
    - model: The model name to use
    - messages: Conversation history
    - objective: The user's objective
    - session_id: Session tracking ID

    Returns:
    - [operations, updated_messages], session_id
    """
    logger.debug("get_next_action started")

    if config.verbose:
        print("[Self-Operating Computer][get_next_action]")
        print("[Self-Operating Computer][get_next_action] model", model)

    # All models now use Groq
    if model in ["gpt-4", "gpt-4-with-ocr", "custom-gpt"]:
        return call_groq_vision(messages), session_id

    if model in ["gpt-4-with-som", "fast-gpt", "fast-gemini", "custom-gemini"]:
        operation = await call_groq_vision_labeled(messages, objective, model)
        return operation, session_id

    if model in ["gemini-pro-vision"]:
        return call_groq_vision(messages), session_id

    if model == "llava":
        return call_groq_vision(messages), session_id

    # Default to Groq vision
    return call_groq_vision(messages), session_id


def call_groq_vision(messages):
    """Call Groq vision model"""
    logger.debug("Calling Groq Vision")
    time.sleep(1)
    client = config.initialize_groq()

    try:
        img_base64, screenshot_path = get_screenshot_base64()

        if len(messages) == 1:
            user_prompt = get_user_first_message_prompt()
        else:
            user_prompt = get_user_prompt()

        vision_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                },
            ],
        }
        messages.append(vision_message)

        response = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=messages,
            max_tokens=1024,
        )

        content = response.choices[0].message.content
        logger.debug("Response received")

        content = clean_json(content)
        assistant_message = {"role": "assistant", "content": content}
        messages.append(assistant_message)

        content = json.loads(content)
        return [content, messages]

    except Exception as e:
        logger.error(f"Groq vision call failed: {e}")
        return [[{"operation": "done", "summary": f"Error: {e}"}], messages]


async def call_groq_vision_labeled(messages, objective, model):
    """Call Groq vision with labeled screenshot (SoM)"""
    logger.debug("Calling Groq Vision with SoM labels")
    client = config.initialize_groq()

    try:
        img_base64, screenshot_path = get_screenshot_base64()

        # Add labels using OmniParser
        labeled_path, content_list = add_labels(screenshot_path)

        with open(labeled_path, "rb") as f:
            labeled_base64 = base64.b64encode(f.read()).decode("utf-8")

        if len(messages) == 1:
            user_prompt = get_user_first_message_prompt()
        else:
            user_prompt = get_user_prompt()

        vision_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{labeled_base64}"},
                },
            ],
        }
        messages.append(vision_message)

        response = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=messages,
            max_tokens=1024,
        )

        content = response.choices[0].message.content
        content = clean_json(content)

        assistant_message = {"role": "assistant", "content": content}
        messages.append(assistant_message)

        operations = json.loads(content)

        # Process click operations to get coordinates from labels
        for op in operations:
            if op.get("operation") == "click" and "label" in op:
                label = op["label"]
                coords = get_click_position_in_percent(label, content_list)
                if coords:
                    op["x"] = coords["x"]
                    op["y"] = coords["y"]

        return [operations, messages]

    except Exception as e:
        logger.error(f"Groq vision labeled call failed: {e}")
        return [[{"operation": "done", "summary": f"Error: {e}"}], messages]
