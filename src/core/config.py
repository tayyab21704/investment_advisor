import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Explicitly load .env from the project root
load_dotenv()

class Settings(BaseSettings):
    """
    Production-grade configuration management.
    Uses Pydantic to enforce type safety for environment variables.
    """
    
    # LLM API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    
    # Database Configuration
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "investment_ai")
    
    # Server Configuration
    port: int = int(os.getenv("PORT", 8000))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Market Logic Thresholds (Industry Standard)
    vix_upper_limit: float = float(os.getenv("VIX_UPPER_LIMIT", 22.0))
    vix_lower_limit: float = float(os.getenv("VIX_LOWER_LIMIT", 15.0))
    sma_window: int = int(os.getenv("SMA_WINDOW", 50))

    # Pydantic configuration to handle .env file priority
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )
    # Inside class Settings(BaseSettings):

    # ... existing market settings ...

    # [NEW] Scout Screening Thresholds
    min_roe_threshold: float = float(os.getenv("MIN_ROE_THRESHOLD", 15.0))
    max_debt_ratio: float = float(os.getenv("MAX_DEBT_RATIO", 1.5))
    
    # [NEW] Risk Thresholds
    max_high_risk_alloc: float = float(os.getenv("MAX_HIGH_RISK_ALLOC", 40.0))

    # CONSERVATIVE (Risk 1-4)
    cons_max_beta: float = float(os.getenv("CONS_MAX_BETA", 0.8))
    cons_max_drawdown: float = float(os.getenv("CONS_MAX_DRAWDOWN", 15.0))
    
    # MODERATE (Risk 5-7)
    mod_max_beta: float = float(os.getenv("MOD_MAX_BETA", 1.1))
    mod_max_drawdown: float = float(os.getenv("MOD_MAX_DRAWDOWN", 25.0))
    
    # AGGRESSIVE (Risk 8-10)
    agg_max_beta: float = float(os.getenv("AGG_MAX_BETA", 1.5))
    agg_max_drawdown: float = float(os.getenv("AGG_MAX_DRAWDOWN", 40.0))

    # SYSTEM-WIDE SAFETY
    max_correlation_threshold: float = float(os.getenv("MAX_CORRELATION", 0.7))

    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "investment_council")
    
    # --- PROFILING DEFAULTS ---
    # The default risk score if calculations fail
    default_risk_capacity: int = 5

# Create a global instance to be used across the project
settings = Settings()