"""
models.py — Pydantic request/response models for Investment Council API.

Original models (untouched):
  - RecommendationRequest
  - PortfolioItem
  - RecommendationResponse

Phase-1 additions (below the separator):
  - SparklinePoint
  - IndexDetail, IndexMapResponse
  - MoverDetail, TopMoversResponse
  - SectorData, SectorsResponse
  - SearchResult, SearchResponse
  - ChartCandle, StockDetail
  - MarketStatusResponse
  - HealthResponse
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# ─── ORIGINAL MODELS ─────────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    user_id: str
    behavioral_answers: List[int] = Field(..., description="List of 1, 2, or 3 scores from behavioral test")


class PortfolioItem(BaseModel):
    ticker: str
    monthly_amount: float
    reasoning: str


class RecommendationResponse(BaseModel):
    recommendation_id: str
    status: str
    iteration_count: int
    portfolio: List[PortfolioItem]
    orchestrator_rationalization: str
    agent_outputs: Dict[str, Any] = Field(..., description="Full reasoning traces from all agents")
    user_profile_summary: Dict[str, Any]


# ─── PHASE-1 MODELS ──────────────────────────────────────────────────────────

# ── Shared primitives ────────────────────────────────────────────────────────

class ChartCandle(BaseModel):
    """Single OHLCV candle for chart data."""
    timestamp: str       # ISO 8601, IST
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: int = 0


# ── /api/market-indices ──────────────────────────────────────────────────────

class IndexDetail(BaseModel):
    """Enriched index payload returned by /api/market-indices."""
    symbol: str
    name: str
    # Kept from v1
    value: float
    change: float
    change_pct: float
    # Phase-1 additions
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    sparkline: List[float] = Field(default_factory=list,
                                   description="~30 closing prices at 15-min interval for mini-chart")
    market_regime: str = "NEUTRAL"   # "BULLISH" | "BEARISH" | "NEUTRAL"
    regime_confidence: float = 0.5   # 0–1


# ── /api/top-movers ──────────────────────────────────────────────────────────

class MoverDetail(BaseModel):
    """Enriched mover entry returned by /api/top-movers."""
    symbol: str
    name: Optional[str] = None
    # Kept from v1
    price: float
    change_pct: float
    # Phase-1 additions
    change: float = 0.0
    volume: int = 0
    avg_volume: int = 0
    volume_surge: bool = False   # True if volume > 1.5× avg_volume
    sector: Optional[str] = None
    sparkline: List[float] = Field(default_factory=list,
                                   description="~20 closing prices at 5-min interval")


class TopMoversResponse(BaseModel):
    gainers: List[MoverDetail]
    losers: List[MoverDetail]


# ── /api/sectors ─────────────────────────────────────────────────────────────

class SectorData(BaseModel):
    """Single sector row in the heatmap."""
    sector_name: str
    change_pct: float        # average 1-day % change
    performance_1w: float    # average 1-week % change
    performance_1m: float    # average 1-month % change
    top_performer: Optional[str] = None
    worst_performer: Optional[str] = None
    market_cap_cr: float = 0.0    # sum of market caps in INR crores


class SectorsResponse(BaseModel):
    sectors: List[SectorData]


# ── /api/search ──────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    """Single search hit from /api/search."""
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    current_price: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap_cr: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total: int


# ── /api/stock/{symbol} ──────────────────────────────────────────────────────

class StockDetail(BaseModel):
    """Comprehensive stock detail payload."""
    # Identity
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None

    # Price (v1 fields kept)
    price: float
    current_price: float
    change: float
    change_pct: float
    open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    prev_close: Optional[float] = None
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    volume: int = 0
    avg_volume: int = 0

    # Fundamentals
    market_cap_cr: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_cr: Optional[float] = None
    profit_cr: Optional[float] = None

    # Multi-timeframe charts
    chart_1d: List[ChartCandle] = Field(default_factory=list)
    chart_1w: List[ChartCandle] = Field(default_factory=list)
    chart_1m: List[ChartCandle] = Field(default_factory=list)
    chart_1y: List[ChartCandle] = Field(default_factory=list)
    chart_5y: List[ChartCandle] = Field(default_factory=list)

    # Legacy chart field (v1 compatibility)
    chart: List[Dict[str, Any]] = Field(default_factory=list)

    # Technicals
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    above_sma_50: Optional[bool] = None
    above_sma_200: Optional[bool] = None

    # Fundamentals (v1 legacy fields)
    market_cap: Optional[float] = None
    pe_ratio_legacy: Optional[float] = None
    roe_legacy: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    debt_equity: Optional[float] = None

    # Sentiment
    regime: str = "NEUTRAL"
    regime_confidence: float = 0.5
    description: Optional[str] = None


# ── /api/market-status ───────────────────────────────────────────────────────

class MarketStatusResponse(BaseModel):
    is_open: bool
    current_time_ist: str                          # ISO 8601 in IST
    session: str                                    # "pre_market" | "open" | "post_market" | "closed"
    next_open: str                                  # ISO 8601, IST


# ── /api/health ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str                                  # ISO 8601, IST

# ── Authentication Models ─────────────────────────────────────────────────────

class UserRegistrationRequest(BaseModel):
    name: str
    email: str
    password: str
    
    # Risk Metrics
    behavioral_risk_score: int
    financial_risk_score: int
    actual_risk_capacity: int
    
    # Financial Data
    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float
    existing_debt: float
    debt_to_income_ratio: float
    
    # Investment Constraints
    liquidity_required_pct: float = 20.0
    max_single_asset_pct: float = 15.0
    max_high_risk_allocation_pct: float = 40.0
    investment_horizon_years: int

class UserLoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user_id: str
    name: str
    email: str

class UserProfileUpdateRequest(BaseModel):
    name: str
    behavioral_risk_score: int
    financial_risk_score: int
    actual_risk_capacity: int
    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float
    existing_debt: float
    debt_to_income_ratio: float
    liquidity_required_pct: float = 20.0
    max_single_asset_pct: float = 15.0
    max_high_risk_allocation_pct: float = 40.0
    investment_horizon_years: int
