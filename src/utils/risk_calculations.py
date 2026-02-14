import numpy as np
from typing import List, Dict

def calculate_portfolio_volatility(assets: List[Dict]) -> float:
    """
    Estimatest portfolio volatility based on asset betas.
    Simplified: Assume market volatility is 15% and use weighted average beta.
    """
    if not assets:
        return 0.0
        
    market_vol = 15.0 # baseline 15%
    betas = [a.get("beta", 1.0) for a in assets]
    avg_beta = sum(betas) / len(betas)
    
    return round(avg_beta * market_vol, 2)

def estimate_max_drawdown(volatility: float) -> float:
    """
    Rule of thumb: Max Drawdown is often ~2x expected annual volatility.
    """
    return round(volatility * 2.0, 2)
