import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(override=True) # Force load .env and override system variables

class Settings(BaseSettings):
    """System settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017" # Default
    MONGO_DB_NAME: str = "investment_ai_langgraph"

    # LLM APIs
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Server
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

settings = Settings()

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
