"""LLM API integrations"""
import os
import json
import base64
import time
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
    os.makedirs("screenshots", exist_ok=True)
    path = "screenshots/screenshot.png"
    capture_screen_with_cursor(path)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), path

def call_groq_vision(messages):
    """Call Groq vision model"""
    logger.debug("Calling Groq")
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
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=1024
        )

        content = clean_json(response.choices[0].message.content)
        messages.append({"role": "assistant", "content": content})

        return [json.loads(content), messages]
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return [[{"operation": "done", "summary": f"Error: {e}"}], messages]

async def get_next_action(model, messages, objective, session_id):
    """Get next action from LLM"""
    return call_groq_vision(messages), session_id
