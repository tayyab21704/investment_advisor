
from enum import Enum
from typing import List, Dict
from pydantic import BaseModel, Field, field_validator


# -----------------------------
# 1. ENUMS (Standardized States)
# -----------------------------
class MarketRegime(str, Enum):
    RISK_ON = "Risk-On"
    RISK_OFF = "Risk-Off"
    TRANSITION = "Transition"
    LATE_CYCLE = "Late Cycle"
    RECOVERY = "Recovery"

class LiquidityState(str, Enum):
    EASING = "Easing"
    NEUTRAL = "Neutral"
    TIGHTENING = "Tightening"

class RiskState(str, Enum):
    LOW = "Low Risk"
    MODERATE = "Moderate Risk"
    HIGH = "High Risk"

# -----------------------------
# 2. CONTRACTS (Strict Validation)
# -----------------------------
class MarketRegimeInput(BaseModel):
    """Normalized macro signals from loader.py"""
    equity_trend_score: float = Field(..., ge=-1, le=1)
    volatility_level: float = Field(..., ge=0, le=1)
    rate_direction: int = Field(..., description="-1: cut, 0: neutral, 1: hike")
    inflation_level: float = Field(..., ge=0, le=1)
    yield_curve_slope: float = Field(...)

    @field_validator("rate_direction")
    @classmethod
    def validate_rates(cls, v):
        if v not in (-1, 0, 1):
            raise ValueError("Must be -1, 0, or 1")
        return v

class MarketRegimeOutput(BaseModel):
    market_regime: MarketRegime
    risk_state: RiskState
    liquidity_state: LiquidityState
    confidence: float = Field(..., ge=0, le=1)
    drivers: List[str]
    raw_scores: Dict[str, float]

#=================================================================
# Tool2
#=================================================================
from typing import Dict, List
from pydantic import BaseModel

class AssetRating(BaseModel):
    """Represents the rating for a single asset class."""
    rating: str # Preferred, Neutral, Avoid, Reject
    confidence: float
    score: float
    reason: str

class AssetSuitabilityOutput(BaseModel):
    """Final output structure for the Asset Suitability Tool."""
    regime: str
    risk_state: str
    asset_class_ratings: Dict[str, AssetRating]

#=================================================================
# Tool3
#=================================================================
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel

class SectorSignal(BaseModel):
    """Detailed signal for an individual market sector."""
    sector_name: str
    recommendation: str # Overweight, Neutral, Underweight
    momentum_score: float
    macro_score: float
    composite_score: float
    reasoning: str

class SectorRotationOutput(BaseModel):
    """The full report output for sector rotation strategy."""
    timestamp: datetime
    sector_signals: Dict[str, SectorSignal]
    rotation_narrative: str
    top_sectors: List[str]
    avoid_sectors: List[str]
    confidence_score: float

#=================================================================
# Tool4
#=================================================================
from datetime import datetime
from typing import List
from pydantic import BaseModel

# -----------------------------
# 1. MODELS
# -----------------------------

class ScannedInstrument(BaseModel):
    """Represents an individual stock candidate that passed the initial screening."""
    ticker: str
    name: str
    sector: str
    composite_score: float
    rank: int
    recommendation_reason: str

class InstrumentScreenerOutput(BaseModel):
    """The finalized list of top-ranked stocks based on technical and fundamental filters."""
    timestamp: datetime
    regime: str
    top_picks: List[ScannedInstrument]

# -----------------------------
# 2. SHARED MAPPINGS
# -----------------------------

# Keep this here so both Tool 3 and Tool 4 can reference standardized sector names
SECTOR_MAP = {
    "IT": ["Technology", "Software", "IT Services", "Information Technology"],
    "Pharma": ["Healthcare", "Pharmaceuticals", "Biotechnology", "Drug Manufacturers"],
    "FMCG": ["Consumer Defensive", "Consumer Goods", "FMCG", "Packaged Foods"],
    "Banking": ["Financial Services", "Banks"],
    "Financial Services": ["Financial Services", "Capital Markets"],
    "Auto": ["Consumer Cyclical", "Auto Manufacturers", "Auto Parts"],
    "Metals": ["Basic Materials", "Steel", "Mining", "Aluminum"],
    "Energy": ["Energy", "Oil & Gas"],
    "Infrastructure": ["Industrials", "Engineering", "Construction", "Infrastructure"],
    "Realty": ["Real Estate"]
}

from typing import List, Dict
from pydantic import BaseModel

# -----------------------------
# TOOL 5: Fundamental Health
# -----------------------------
class SanityCheckResult(BaseModel):
    """Deep-dive audit of financial safety and red flags."""
    ticker: str
    pass_status: bool  # True = Passed, False = Failed
    health_score: float  # 0 to 100
    red_flags: List[str]
    audit_remark: str

# -----------------------------
# TOOL 6: Valuation Audit
# -----------------------------
class ValuationResult(BaseModel):
    """Analysis of price justification using PE, PEG, and PB ratios."""
    ticker: str
    valuation_status: str  # Undervalued, Fair, Expensive, Bubble
    valuation_score: float
    is_safe_to_buy: bool
    metrics: Dict[str, float]
    remark: str

# -----------------------------
# TOOL 7: Opportunity Cost
# -----------------------------
class OppCostResult(BaseModel):
    """Efficiency check to ensure the stock outperforms risk-free bonds."""
    ticker: str
    stock_expected_return: float
    hurdle_rate: float
    opportunity_gain_loss: float
    verdict: str  # 'Alpha Generator' or 'Capital Waster'

# -----------------------------
# TOOL 8: Forward Risk
# -----------------------------
class ForwardAudit(BaseModel):
    """Analyst price target and EPS growth viability analysis."""
    ticker: str
    growth_outlook: str
    forward_risk_score: float
    upside_potential: float
    verdict: str

# -----------------------------
# TOOL 9: Social Sentiment
# -----------------------------
class SentimentAudit(BaseModel):
    """NLP-based quantification of crowd emotion and news buzz."""
    ticker: str
    sentiment_score: float  # -1 to 1
    crowd_status: str       # Bullish, Bearish, or Neutral
    is_overhyped: bool
    verdict: str