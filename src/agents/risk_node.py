import logging
from src.core.state import InvestmentState
from src.utils.risk_calculations import calculate_portfolio_volatility, estimate_max_drawdown

logger = logging.getLogger("RiskNode")

async def risk_node(state: InvestmentState) -> InvestmentState:
    """
    Node: Risk Guardian.
    Validates the scout recommendations against user risk limits.
    """
    logger.info("--- NODE: Risk ---")
    profile = state["user_profile"]
    recs = state["scout_recommendations"]
    
    if not recs:
        state["risk_assessment"] = {"verdict": "MODIFY", "issue": "No recommendations found."}
        return state

    # 1. Calculate Portfolio Volatility & Drawdown
    volatility = calculate_portfolio_volatility(recs)
    est_drawdown = estimate_max_drawdown(volatility)
    
    # 2. Compare with User Limits
    max_limit = profile.get("max_drawdown_pct", 15)
    
    issues = []
    if est_drawdown > max_limit:
        issues.append(f"Estimated drawdown ({est_drawdown}%) exceeds limit ({max_limit}%).")
        
    # Check for High-Risk Over-allocation (Crypto)
    high_risk_assets = [r for r in recs if "BTC" in r["ticker"] or "ETH" in r["ticker"]]
    high_risk_weight = (len(high_risk_assets) / len(recs)) * 100 if recs else 0
    
    if high_risk_weight > profile.get("max_high_risk_allocation_pct", 10):
        issues.append(f"High-risk allocation ({round(high_risk_weight)}%) exceeds limit.")

    # 3. Decision
    if issues:
        verdict = "MODIFY"
        reasoning = f"Safety limits breached: {' '.join(issues)}"
    else:
        verdict = "APPROVE"
        reasoning = f"Portfolio risk (Drawdown: {est_drawdown}%) is within user tolerance."

    # 4. Update State
    risk_assessment = {
        "verdict": verdict,
        "issue": reasoning,
        "volatility": volatility,
        "est_drawdown": est_drawdown,
        "high_risk_weight": high_risk_weight
    }
    
    state["risk_assessment"] = risk_assessment
    state["agent_outputs"]["risk"] = {
        "verdict": verdict,
        "metrics": risk_assessment
    }
    
    return state
