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
    
    # ============================================
    # LLM API KEYS
    # ============================================
    # Primary Key (Required)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    
    # Backup Keys (Optional) - FIX: Added type annotations to prevent Pydantic crash
    groq_api_key_2: Optional[str] = os.getenv("GROQ_API_KEY_2")
    groq_api_key_3: Optional[str] = os.getenv("GROQ_API_KEY_3")
    
    # Fallback Engine
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "investment_ai")
    
    # ============================================
    # SERVER CONFIGURATION
    # ============================================
    port: int = int(os.getenv("PORT", 8000))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ============================================
    # MARKET INTELLIGENCE THRESHOLDS
    # ============================================
    vix_upper_limit: float = float(os.getenv("VIX_UPPER_LIMIT", 22.0))
    vix_lower_limit: float = float(os.getenv("VIX_LOWER_LIMIT", 15.0))
    sma_window: int = int(os.getenv("SMA_WINDOW", 50))
    
    # ============================================
    # SCOUT SCREENING THRESHOLDS
    # ============================================
    min_roe_threshold: float = float(os.getenv("MIN_ROE_THRESHOLD", 15.0))
    max_debt_ratio: float = float(os.getenv("MAX_DEBT_RATIO", 1.5))
    
    # ============================================
    # RISK GUARDIAN LIMITS
    # ============================================
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
    
    # ============================================
    # PERSONALIZATION DEFAULTS
    # ============================================
    # Liquidity Reserve: % of monthly surplus to keep as emergency fund
    default_liquidity_required_pct: float = float(os.getenv("DEFAULT_LIQUIDITY_PCT", 20.0))
    
    # Max Per Asset: Maximum % allocation to any single asset
    default_max_single_asset_pct: float = float(os.getenv("DEFAULT_MAX_ASSET_PCT", 15.0))
    
    # Portfolio Concentration: Min number of assets recommended
    min_portfolio_assets: int = int(os.getenv("MIN_PORTFOLIO_ASSETS", 5))
    max_portfolio_assets: int = int(os.getenv("MAX_PORTFOLIO_ASSETS", 10))
    
    # ============================================
    # PROFILING NODE DEFAULTS
    # ============================================
    # Investment Horizon: Default years if not specified
    default_investment_horizon_years: int = int(os.getenv("DEFAULT_HORIZON_YEARS", 10))
    
    # Debt Safety: Debt-to-Income ratio thresholds
    high_debt_threshold: float = float(os.getenv("HIGH_DEBT_THRESHOLD", 0.4))
    critical_debt_threshold: float = float(os.getenv("CRITICAL_DEBT_THRESHOLD", 0.6))
    
    # Emergency Fund: Months of expenses to keep liquid
    min_emergency_fund_months: int = int(os.getenv("MIN_EMERGENCY_MONTHS", 3))
    recommended_emergency_fund_months: int = int(os.getenv("REC_EMERGENCY_MONTHS", 6))
    
    # ============================================
    # ORCHESTRATOR DEBATE SETTINGS
    # ============================================
    # Max Debate Rounds: How many times orchestrator can loop back
    max_debate_iterations: int = int(os.getenv("MAX_DEBATE_ITERATIONS", 3))
    
    # Confidence Threshold: Min confidence to approve without debate
    min_confidence_auto_approve: float = float(os.getenv("MIN_CONFIDENCE_APPROVE", 0.8))
    
    # ============================================
    # PYDANTIC CONFIGURATION
    # ============================================
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Create a global instance to be used across the project
settings = Settings()