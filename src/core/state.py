from typing import TypedDict, List, Dict, Any, Optional

class InvestmentState(TypedDict):
    """
    State definition for the Investment Advisor.
    Flows through all LangGraph nodes.
    """
    # === USER INPUT ===
    user_id: str
    behavioral_answers: List[int]
    
    # === AGENT OUTPUTS ===
    user_profile: Optional[Dict[str, Any]]
    market_context: Optional[Dict[str, Any]]
    scout_recommendations: Optional[List[Dict[str, Any]]]
    risk_assessment: Optional[Dict[str, Any]]
    final_portfolio: Optional[List[Dict[str, Any]]]
    orchestrator_decision: Optional[Dict[str, Any]]
    
    # === TRACKING & CONTROL ===
    agent_outputs: Dict[str, Any]  # Full traces from all agents
    iteration: int                  # Loop counter (0 = first run)
    decision: str                   # PENDING, APPROVED, REJECTED, CONTINUE_DEBATE
    error: Optional[str]            # Error message if something fails
    
    # === FEEDBACK LOOPS ===
    feedback_for_scout: Optional[str]  # Specific guidance for Scout on revision


# === TYPED SUBDICTIONARIES (For Better Type Safety) ===

class UserProfile(TypedDict):
    """
    User's complete risk and financial profile.
    Populated by Profiling Node.
    """
    # === RISK SCORES ===
    behavioral_risk_score: int        # 1-10 from behavioral questions
    financial_risk_score: int         # 1-10 from financial analysis
    actual_risk_capacity: int         # min(behavioral, financial)
    
    # === FINANCIAL DATA ===
    monthly_income: float             # ₹ per month
    monthly_expenses: float           # ₹ per month
    monthly_surplus: float            # income - expenses
    existing_debt: float              # Total debt ₹
    debt_to_income_ratio: float       # debt / (monthly_income * 12)
    
    # === INVESTMENT CONSTRAINTS ===
    liquidity_required_pct: float     # % to keep as emergency fund (default: 20)
    max_single_asset_pct: float       # Max % per asset (default: 15)
    max_high_risk_allocation_pct: float  # Max % in crypto/volatile assets (default: 40)
    investment_horizon_years: int     # Time horizon (e.g., 10 years)
    
    # === RISK LIMITS (Based on risk tier) ===
    max_drawdown_pct: float           # Max acceptable portfolio loss %
    max_beta: float                   # Max portfolio beta vs market
    
    # === WARNINGS ===
    risk_mismatch_warning: Optional[str]  # If behavioral vs financial differ >3


class MarketContext(TypedDict):
    """
    Market regime and indicators.
    Populated by Market Node.
    """
    regime: str                       # RISK_ON, RISK_OFF, NEUTRAL
    confidence: float                 # 0.0-1.0
    raw_analysis: str                 # LLM's reasoning
    indicators: Dict[str, Any]        # VIX, Nifty, SMA, etc.
    sector_breadth: Optional[Dict[str, str]]  # Sector-wise trends


class ScoutRecommendation(TypedDict):
    """
    Single asset recommendation from Scout.
    """
    ticker: str                       # e.g., "TCS.NS"
    name: str                         # e.g., "Tata Consultancy Services"
    type: str                         # "equity", "crypto", "commodity", "debt"
    sector: Optional[str]             # e.g., "IT"
    quality_score: Optional[float]    # 0-100 composite score
    price: Optional[float]            # Current price
    pe: Optional[float]               # Price-to-Earnings ratio
    roe: Optional[float]              # Return on Equity %
    reasoning: Optional[str]          # Why Scout picked this


class RiskAssessment(TypedDict):
    """
    Risk audit results from Risk Guardian.
    """
    verdict: str                      # "APPROVE" or "REJECT"
    metrics: Dict[str, float]         # Beta, volatility, VaR, max_drawdown
    reasoning: str                    # Why approved/rejected
    feedback: Optional[str]           # Specific guidance if rejected
    confidence: float                 # 0.0-1.0


class FinalPortfolioAsset(TypedDict):
    """
    Single asset in the final allocated portfolio.
    Populated by Personalization Node.
    """
    ticker: str
    name: str
    monthly_investment: float         # ₹ amount per month
    allocation_pct: float             # % of investable amount
    type: str                         # "equity", "crypto", etc.
    reasoning: str                    # Why this allocation


class OrchestratorDecision(TypedDict):
    """
    Meta-decision from Orchestrator Debate Node.
    """
    decision: str                     # "APPROVED", "REJECTED", "CONTINUE_DEBATE"
    reasoning: str                    # LLM's full analysis
    confidence: float                 # 0.0-1.0
    iteration: int                    # Which debate round