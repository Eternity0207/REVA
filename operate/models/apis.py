"""LLM API integrations"""
import os
import json
import base64
from loguru import logger
from operate.config import Config
from operate.exceptions import ModelNotRecognizedException

config = Config()

GROQ_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def clean_json(content):
    """Clean JSON from LLM response"""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return content.strip()
