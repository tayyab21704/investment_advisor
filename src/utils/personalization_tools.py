import logging
from typing import List, Dict, Any
from src.core.config import settings

logger = logging.getLogger(__name__)

def calculate_investable_amount(
    monthly_surplus: float,
    liquidity_required_pct: float
) -> Dict[str, float]:
    """
    Calculates the actual money available for investment after setting aside a liquidity reserve.
    
    Args:
        monthly_surplus (float): The total monthly savings available (₹).
        liquidity_required_pct (float): Percentage of surplus to keep as an emergency fund (e.g., 20.0).
    
    Returns:
        Dict[str, float]: A dictionary containing 'liquidity_reserve', 'investable_amount', and 'total_surplus'.
    """
    liquidity_reserve = monthly_surplus * (liquidity_required_pct / 100)
    investable_amount = monthly_surplus - liquidity_reserve
    
    return {
        "liquidity_reserve": round(liquidity_reserve, 2),
        "investable_amount": round(investable_amount, 2),
        "total_surplus": round(monthly_surplus, 2)
    }


def validate_allocation(
    allocations: List[Dict[str, Any]],
    investable_amount: float,
    max_single_asset_pct: float
) -> Dict[str, Any]:
    """
    Checks if a proposed portfolio allocation follows the user's safety constraints.
    
    Args:
        allocations (List[Dict]): List of assets with 'ticker', 'monthly_investment', and 'allocation_pct'.
        investable_amount (float): Total ₹ available for the monthly SIP.
        max_single_asset_pct (float): The maximum allowed percentage for a single asset (e.g., 15.0).
    
    Returns:
        Dict[str, Any]: Results containing 'valid' (bool), 'violations' (list), and 'utilization_pct'.
    """
    violations = []
    total_allocated = 0.0
    
    for asset in allocations:
        monthly_amt = asset.get("monthly_investment", 0)
        allocation_pct = asset.get("allocation_pct", 0)
        ticker = asset.get("ticker", "Unknown")
        
        # Check 1: Math Consistency
        expected_amt = investable_amount * (allocation_pct / 100)
        if abs(monthly_amt - expected_amt) > 1.0:
            violations.append(f"{ticker}: Amount ₹{monthly_amt} doesn't match {allocation_pct}% of total.")
        
        # Check 2: Concentration Risk
        if allocation_pct > max_single_asset_pct:
            violations.append(f"{ticker}: {allocation_pct}% exceeds the {max_single_asset_pct}% limit.")
        
        total_allocated += monthly_amt
    
    # Check 3: Budget Integrity
    if abs(total_allocated - investable_amount) > 5.0:
        violations.append(f"Total allocated ₹{total_allocated} does not equal budget ₹{investable_amount}.")
    
    return {
        "valid": len(violations) == 0,
        "total_allocated": round(total_allocated, 2),
        "violations": violations,
        "utilization_pct": round((total_allocated / investable_amount) * 100, 2) if investable_amount > 0 else 0
    }


def suggest_allocation_strategy(
    risk_score: int,
    asset_types: List[str]
) -> Dict[str, Any]:
    """
    Provides a recommended weight distribution (Equity vs Crypto vs Debt) based on a 1-10 risk score.
    
    Args:
        risk_score (int): User's risk capacity from 1 (Conservative) to 10 (Aggressive).
        asset_types (List[str]): The types of assets found in the portfolio (e.g., ["equity", "crypto"]).
    """
    if risk_score <= 4:
        strategy = "conservative"
        base_weights = {"equity": 60, "crypto": 5, "commodity": 15, "debt": 20}
        reasoning = "Prioritize stability and capital preservation."
    elif risk_score <= 7:
        strategy = "moderate"
        base_weights = {"equity": 70, "crypto": 15, "commodity": 10, "debt": 5}
        reasoning = "Balanced growth with controlled exposure to volatility."
    else:
        strategy = "aggressive"
        base_weights = {"equity": 75, "crypto": 20, "commodity": 5, "debt": 0}
        reasoning = "Focus on high growth and capital appreciation."
    
    recommendations = {t: base_weights.get(t, 0) for t in asset_types}
    
    # Normalize to 100%
    total = sum(recommendations.values())
    if total > 0:
        recommendations = {k: round((v / total) * 100, 2) for k, v in recommendations.items()}
    
    return {"strategy": strategy, "recommendations": recommendations, "reasoning": reasoning}


def allocate_equal_weight(
    assets: List[Dict[str, Any]],
    investable_amount: float,
    max_single_asset_pct: float
) -> List[Dict[str, Any]]:
    """
    A safe fallback tool that distributes the budget equally across all selected assets.
    
    Args:
        assets (List[Dict]): Tickers and metadata from the Scout Agent.
        investable_amount (float): Total ₹ to be distributed.
        max_single_asset_pct (float): Maximum allowed weight per asset.
    """
    num_assets = len(assets)
    if num_assets == 0: return []
    
    equal_pct = min(100 / num_assets, max_single_asset_pct)
    allocated_portfolio = []
    
    for asset in assets:
        monthly_amt = (investable_amount * equal_pct) / 100
        allocated_portfolio.append({
            "ticker": asset.get("ticker"),
            "name": asset.get("name", asset.get("ticker")),
            "monthly_investment": round(monthly_amt, 2),
            "allocation_pct": round(equal_pct, 2),
            "type": asset.get("type", "equity"),
            "reasoning": f"Equal weight allocation capped at {equal_pct}%."
        })
    
    return allocated_portfolio