"""LLM API integrations"""
import os
import json
import base64
import time
import re
import requests
from loguru import logger
from operate.config import Config
from operate.exceptions import ModelNotRecognizedException
from operate.utils.screenshot import capture_screen_with_cursor
from operate.models.prompts import get_user_prompt, get_user_first_message_prompt

config = Config()

OMNIPARSER_URL = os.getenv("OMNIPARSER_URL", "http://localhost:8001")
GROQ_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def clean_json(content):
    """Extract JSON array from LLM response"""
    content = content.strip()

    # Method 1: Find JSON array with regex
    patterns = [
        r'\[\s*\{[\s\S]*?\}\s*\]',  # [{...}]
        r'\[[\s\S]*?\](?=\s*$)',         # Array at end
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            try:
                json.loads(match.group(0))
                return match.group(0)
            except:
                continue

    # Method 2: Code block extraction
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1]

    return content.strip()

def get_screenshot_base64():
    os.makedirs("screenshots", exist_ok=True)
    path = "screenshots/screenshot.png"
    capture_screen_with_cursor(path)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), path

def add_labels(screenshot_path):
    try:
        with open(screenshot_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        resp = requests.post(f"{OMNIPARSER_URL}/label/",
                           json={"base64_image": img_b64}, timeout=30)

        if resp.status_code == 200:
            result = resp.json()
            labeled_path = screenshot_path.replace(".png", "_labeled.png")
            if "labeled_image" in result:
                with open(labeled_path, "wb") as f:
                    f.write(base64.b64decode(result["labeled_image"]))
            return labeled_path, result.get("parsed_content_list", [])
    except Exception as e:
        logger.warning(f"OmniParser unavailable: {e}")
    return screenshot_path, []

def call_groq_vision(messages):
    logger.debug("Calling Groq Vision")
    time.sleep(1)
    client = config.initialize_groq()

    try:
        img_b64, _ = get_screenshot_base64()
        prompt = get_user_first_message_prompt() if len(messages) == 1 else get_user_prompt()

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        })

        response = client.chat.completions.create(
            model=GROQ_MODEL, messages=messages, max_tokens=1024
        )

        raw_content = response.choices[0].message.content
        content = clean_json(raw_content)

        try:
            operations = json.loads(content)
            if not isinstance(operations, list):
                operations = [operations]
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}\nRaw: {raw_content}")
            operations = [{"operation": "done", "summary": "Parse error"}]

        messages.append({"role": "assistant", "content": content})
        return [operations, messages]

    except Exception as e:
        logger.error(f"API call failed: {e}")
        return [[{"operation": "done", "summary": f"Error: {e}"}], messages]

async def get_next_action(model, messages, objective, session_id):
    return call_groq_vision(messages), session_id
