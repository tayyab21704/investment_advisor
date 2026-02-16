import os
import logging
from typing import Dict, Any, List

# Standard logging setup for the utility module
logger = logging.getLogger(__name__)

def analyze_loss_aversion(questionnaire_responses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes user responses to detect loss aversion and panic behavior.
    Uses keyword detection to identify emotional responses to market stress.
    """
    flags = []
    score_penalty = 0
    
    # Convert all responses to a single string for robust keyword searching
    responses_str = str(questionnaire_responses).lower()
    
    # Check for panic selling tendencies (e.g., "sell everything", "stop losses")
    if "sell everything" in responses_str or "stop losses" in responses_str:
        flags.append("panic_seller")
        score_penalty += 2
        
    # Check for anxiety regarding volatility (e.g., "anxious", "fluctuations")
    if "anxious" in responses_str or "fluctuations" in responses_str:
        flags.append("high_anxiety")
        score_penalty += 1

    # Check for historical patterns of panic behavior
    if "exited" in responses_str or "crash" in responses_str:
        flags.append("history_of_panic_selling")
        score_penalty += 2

    return {
        "behavioral_flags": flags,
        "risk_penalty": score_penalty,
        "analysis": "User shows signs of loss aversion." if flags else "User appears resilient."
    }

def analyze_income_stability(annual_income: float, debt_amount: float, job_type: str, emergency_fund_months: int) -> Dict[str, Any]:
    """
    Calculates financial stability based on income, debt, and emergency funds.
    This provides the quantitative 'capacity' to take risk.
    """
    # Calculate Debt-to-Income (DTI) ratio
    debt_to_income = 0
    if annual_income > 0:
        debt_to_income = debt_amount / annual_income

    # Determine liquidity needs based on emergency fund buffer
    liquidity_needs = "LOW"
    if emergency_fund_months < 6:
        liquidity_needs = "HIGH"
    elif emergency_fund_months < 12:
        liquidity_needs = "MEDIUM"

    # Stability Score calculation (Starting at 10)
    stability_score = 10
    
    # Adjust for job type (Freelance/Self-Employed is considered less stable)
    if str(job_type).lower() in ["freelance", "self-employed"]:
        stability_score -= 2
        
    # Penalty for high debt-to-income ratio
    if debt_to_income > 0.4:
        stability_score -= 3
        
    # Penalty for high liquidity needs (low emergency fund)
    if liquidity_needs == "HIGH":
        stability_score -= 2

    return {
        "debt_to_income": round(debt_to_income, 2),
        "liquidity_needs": liquidity_needs,
        "stability_score": stability_score,
        "status": "STABLE" if stability_score > 6 else "UNSTABLE"
    }

def calculate_final_risk_score(demographic_risk_base: int, behavioral_penalty: int, stability_score: int) -> int:
    """
    Combines demographic data with behavioral analysis to generate the final 1-10 risk score.
    Logic: Behavioral panic signals and financial instability reduce the final capacity.
    """
    # Start with the demographic base score (usually age-based) and subtract behavioral penalties
    raw_score = demographic_risk_base - behavioral_penalty
    
    # If the user is financially unstable, drop the risk capacity further
    if stability_score < 5:
        raw_score -= 2
        
    # Clamp the final score between 1 (Minimum) and 10 (Maximum)
    final_score = max(1, min(10, raw_score))
    
    return int(final_score)