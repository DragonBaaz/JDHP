"""
config.py — Configuration with validation
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class ConfigError(Exception):
    """Raised when required environment variables are missing or invalid."""
    pass

class Config:
    def __init__(self):
        """Initialize configuration and validate all required environment variables."""
        self.ANTHROPIC_API_KEY = self._get_required(
            "ANTHROPIC_API_KEY",
            "Anthropic API key from console.anthropic.com/settings/keys"
        )
        self.GUMROAD_ACCESS_TOKEN = self._get_required(
            "GUMROAD_ACCESS_TOKEN",
            "Gumroad API token from app.gumroad.com/settings/advanced"
        )
        self.EXCHANGERATE_API_KEY = self._get_required(
            "EXCHANGERATE_API_KEY",
            "Free tier from exchangerate-api.com"
        )
        
        # Optional overrides with defaults
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DB_PATH = os.getenv("DB_PATH", "jdhp.db")
        self.OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

    def _get_required(self, key: str, help_text: str) -> str:
        """Helper method to get and validate required environment variables."""
        val = os.environ.get(key)
        if not val or not val.strip():
            raise ConfigError(
                f"Missing required environment variable: {key}\n"
                f"  How to get it: {help_text}\n"
                f"  Add to your .env file (copy from .env.example)\n"
            )
        return val.strip()

try:
    config = Config()
except ConfigError as e:
    print(f"\n❌ Configuration Error:\n{e}\n", file=sys.stderr)
    print("Please copy .env.example to .env and fill in your API keys.\n", file=sys.stderr)
    sys.exit(1)