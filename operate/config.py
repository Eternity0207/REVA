"""Configuration management"""
import os
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
        load_dotenv()
        self.verbose = False
        self.api_key = None

    def initialize_groq(self):
        """Initialize Groq client"""
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")
        logger.debug(f"Initializing client: {base_url}")
        return OpenAI(api_key=api_key, base_url=base_url)

    def validation(self, model, voice_mode):
        """Check if API key is configured"""
        return not bool(os.getenv("OPENAI_API_KEY"))
