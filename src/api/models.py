from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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
