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
