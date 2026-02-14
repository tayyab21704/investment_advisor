import logging
from src.core.state import InvestmentState

logger = logging.getLogger("PersonalizationNode")

async def personalization_node(state: InvestmentState) -> InvestmentState:
    """
    Node: Personalization.
    Calculates exact ₹ monthly allocations based on surplus and liquidity.
    """
    logger.info("--- NODE: Personalization ---")
    profile = state["user_profile"]
    recs = state["scout_recommendations"]
    
    # 1. Financial Constants
    monthly_surplus = float(profile.get("monthly_surplus", 0))
    liquidity_reserve_pct = float(profile.get("liquidity_required_pct", 20))
    
    # 2. Calculate Investable Amount
    investment_budget = monthly_surplus * (1 - (liquidity_reserve_pct / 100))
    
    if not recs:
        state["final_portfolio"] = []
        return state
        
    # 3. Allocation Strategy: Equal weight for simplicity, capped by single asset limit
    num_assets = len(recs)
    allocation_per_asset = investment_budget / num_assets
    
    max_single_limit = (profile.get("max_single_asset_pct", 25) / 100) * investment_budget
    safe_allocation = min(allocation_per_asset, max_single_limit)
    
    portfolio = []
    for r in recs:
        portfolio.append({
            "ticker": r["ticker"],
            "monthly_amount": round(safe_allocation, 2),
            "reasoning": r.get("reasoning", "Matches risk profile.")
        })
        
    # 4. Update State
    state["final_portfolio"] = portfolio
    state["agent_outputs"]["personalization"] = {
        "verdict": "COMPLETE",
        "budget": round(investment_budget, 2),
        "reserve": round(monthly_surplus - investment_budget, 2),
        "portfolio": portfolio
    }
    
    return state
