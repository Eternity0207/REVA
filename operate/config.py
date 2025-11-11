import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger


class Config:
    """
    Configuration class for managing settings.
    Uses Groq API via OpenAI-compatible interface.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        load_dotenv()
        self.verbose = False
        self.api_key = None  # Cache for API key

    def initialize_groq(self):
        """Initialize OpenAI client pointing to Groq API."""
        if self.verbose:
            print("[Config][initialize_groq]")

        if self.api_key:
            api_key = self.api_key
            logger.debug("Using cached API key")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            logger.debug(f"API key loaded from env")

        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        logger.debug(f"Using API base URL: {base_url}")
        return client

    def validation(self, model, voice_mode):
        """Validate that API key exists."""
        key_exists = bool(os.environ.get("OPENAI_API_KEY"))
        if not key_exists:
            print("Error: OPENAI_API_KEY not found in environment")
            return True
        return False

    def save_api_key(self, model, key_value):
        """Save API key to .env file."""
        if key_value is None:
            sys.exit("Operation cancelled by user.")

        if key_value:
            self.api_key = key_value
            self.save_api_key_to_env("OPENAI_API_KEY", key_value)
            load_dotenv()

    @staticmethod
    def save_api_key_to_env(key_name, key_value):
        with open(".env", "a") as file:
            file.write(f"\n{key_name}='{key_value}'")
