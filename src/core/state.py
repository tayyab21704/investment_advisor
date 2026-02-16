from typing import TypedDict, List, Dict, Any, Optional

class InvestmentState(TypedDict):
    """
    State definition for the Investment Advisor.
    """
    user_id: str
    behavioral_answers: List[int]
    
    # Processed Data
    user_profile: Optional[Dict[str, Any]]
    market_context: Optional[Dict[str, Any]]
    scout_recommendations: Optional[List[Dict[str, Any]]]
    risk_assessment: Optional[Dict[str, Any]]
    final_portfolio: Optional[List[Dict[str, Any]]]
    
    # Tracking
    agent_outputs: Dict[str, Any]
    iteration: int
    decision: str # PENDING, APPROVED, REJECTED, CONTINUE_DEBATE
    orchestrator_decision: Optional[Dict[str, Any]]
    error: Optional[str]
    
    # Optional: Keep the raw data for transparency/debugging
    raw_user_data: Optional[Dict[str, Any]]
    
    # Other existing fields (market_context, scout_recommendations, etc.)

    # ... existing fields ...

    # [NEW] The output from the Scout Agent
    scout_recommendations: Optional[List[Dict[str, Any]]]

    # [NEW] Feedback from the Orchestrator (used for Loop 2)
    orchestrator_decision: Optional[Dict[str, Any]]

    # [NEW] Tracks how many times we've looped back (0 = first run)
    iteration: int
    # [RISK AGENT OUTPUTS]
    # Stores the full audit report (Volatility, Beta, VaR, Reasoning)
    risk_assessment: Optional[Dict[str, Any]]
    
    # The final flag used by the Graph to route traffic ("APPROVE" vs "REJECT")
    decision: Optional[str] 
    
    # [FEEDBACK LOOP TRACKING]
    # Stores the specific critique to send back to Scout (e.g., "Too much Crypto")
    feedback_for_scout: Optional[str]

# Add this to your existing state.py
class MarketContext(TypedDict):
    regime: str  # RISK_ON, RISK_OFF, NEUTRAL
    confidence: float
    indicators: Dict[str, Any]
    sector_breadth: Dict[str, str]