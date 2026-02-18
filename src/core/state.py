from typing import TypedDict, List, Dict, Any, Optional

# === TYPED SUBDICTIONARIES ===

class ScoutFeedback(TypedDict):
    """
    Structured feedback for the Scout Agent to improve recommendations.
    """
    violation_type: str        # e.g., "High Beta", "Sector Concentration"
    offending_tickers: List[str] # Specific tickers that failed the audit
    suggested_action: str      # Instructions for the next iteration

class UserProfile(TypedDict):
    """
    User's complete risk and financial profile.
    Populated by Profiling Node.
    """
    # Risk Scores
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
    liquidity_required_pct: float     # Default: 20%
    max_single_asset_pct: float       # Default: 15%
    max_high_risk_allocation_pct: float  # Default: 40%
    investment_horizon_years: int     
    
    # Risk Limits (Tier-based)
    max_drawdown_pct: float           
    max_beta: float                   
    
    risk_mismatch_warning: Optional[str]

class MarketContext(TypedDict):
    """
    Market regime and indicators.
    Populated by Market Node.
    """
    regime: str                       # RISK_ON, RISK_OFF, NEUTRAL
    confidence: float                 
    raw_analysis: str                 
    indicators: Dict[str, Any]        
    sector_breadth: Optional[Dict[str, str]]

class ScoutRecommendation(TypedDict):
    """
    Single asset recommendation from Scout.
    """
    ticker: str                       
    name: str                         
    type: str                         # equity, crypto, commodity, debt
    sector: Optional[str]             
    quality_score: Optional[float]    
    price: Optional[float]            
    pe: Optional[float]               
    roe: Optional[float]              
    reasoning: Optional[str]          

class RiskAssessment(TypedDict):
    """
    Risk audit results from Risk Guardian.
    """
    verdict: str                      # "APPROVE" or "REJECT"
    metrics: Dict[str, float]         
    reasoning: str                    
    feedback: Optional[str]           
    confidence: float                 

class FinalPortfolioAsset(TypedDict):
    """
    Single asset in the final allocated portfolio.
    """
    ticker: str
    name: str
    monthly_investment: float         
    allocation_pct: float             
    type: str                         
    reasoning: str                    

class OrchestratorDecision(TypedDict):
    """
    Meta-decision from Orchestrator Node.
    """
    decision: str                     # "APPROVED", "REJECTED", "CONTINUE_DEBATE"
    reasoning: str                    
    confidence: float                 
    iteration: int                    

# === MAIN STATE DEFINITION ===

class InvestmentState(TypedDict):
    """
    State definition for the Investment Advisor.
    Flows through all LangGraph nodes.
    """
    # User Input
    user_id: str
    behavioral_answers: List[int]
    raw_user_data: Optional[Dict[str, Any]] # NEW: Persists original MongoDB/User data
    
    # Agent Results
    user_profile: Optional[UserProfile]
    market_context: Optional[MarketContext]
    scout_recommendations: Optional[List[ScoutRecommendation]]
    risk_assessment: Optional[RiskAssessment]
    final_portfolio: Optional[List[FinalPortfolioAsset]]
    orchestrator_decision: Optional[OrchestratorDecision]
    
    # Tracking & Control
    agent_outputs: Dict[str, Any]  
    iteration: int                  # 0 = first run
    decision: str                   # PENDING, APPROVED, REJECTED, CONTINUE_DEBATE
    error: Optional[str]            
    
    # Feedback Loop (Structured)
    feedback_for_scout: Optional[ScoutFeedback] # NEW: Structured correction directive