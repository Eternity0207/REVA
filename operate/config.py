"""Configuration management"""
import os
import sys
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

class Config:
    _instance: Optional["Config"] = None
    verbose: bool = False
    api_key: Optional[str] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if os.path.exists(".env"):
            load_dotenv()
        self.verbose = False
        self.api_key = None

    def initialize_groq(self) -> OpenAI:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")
        return OpenAI(api_key=api_key, base_url=base_url)

    def validation(self, model: str, voice_mode: bool) -> bool:
        return not bool(os.getenv("OPENAI_API_KEY"))

    def save_api_key(self, model: str, key_value: str) -> None:
        if not key_value:
            return
        self.api_key = key_value
        with open(".env", "w") as f:
            f.write(f"OPENAI_API_KEY='{key_value}'\n")
            f.write("OPENAI_API_BASE_URL='https://api.groq.com/openai/v1'\n")
        load_dotenv(override=True)
        logger.info("API key saved")
