import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN: str = os.environ["GITHUB_TOKEN"]           # Replaces ANTHROPIC_API_KEY
    GUMROAD_ACCESS_TOKEN: str = os.environ["GUMROAD_ACCESS_TOKEN"]
    EXCHANGERATE_API_KEY: str = os.environ["EXCHANGERATE_API_KEY"]
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH: str = os.getenv("DB_PATH", "jdhp.db")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

config = Config()
