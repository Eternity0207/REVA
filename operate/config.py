"""Configuration management"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if os.path.exists(".env"):
            load_dotenv()
        self.verbose = False
        self.api_key = None

    def initialize_groq(self):
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")
        if not api_key:
            logger.warning("No API key found")
        return OpenAI(api_key=api_key, base_url=base_url)

    def validation(self, model, voice_mode):
        return not bool(os.getenv("OPENAI_API_KEY"))

    def save_api_key(self, model, key_value):
        if not key_value:
            return
        self.api_key = key_value
        with open(".env", "a") as f:
            f.write(f"\nOPENAI_API_KEY='{key_value}'\n")
        load_dotenv(override=True)
