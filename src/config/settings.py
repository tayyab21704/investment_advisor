"""Configuration and settings - loads from environment."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.env = os.getenv('APP_ENV', 'development')
        self.debug = self.env == 'development'
        
        # API Configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.ai_engine_type = os.getenv('AI_ENGINE_TYPE', '').lower()
        
        # Validation
        if self.ai_engine_type == 'gemini' and not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY not set in .env file. "
                "Get it from https://ai.google.dev/ or set AI_ENGINE_TYPE to empty to skip"
            )
        
        if self.ai_engine_type == 'openai' and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY not set in .env file. "
                "Get it from https://platform.openai.com/ or set AI_ENGINE_TYPE to empty to skip"
            )

settings = Settings()
