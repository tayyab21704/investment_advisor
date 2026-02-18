import logging
from typing import Dict, List, Any, Optional
from src.core.state import ScoutFeedback, RiskAssessment, UserProfile, MarketContext

logger = logging.getLogger("OrchestratorUtils")

def detect_strategy_conflicts(
    market: MarketContext, 
    risk: RiskAssessment, 
    profile: UserProfile
) -> Optional[ScoutFeedback]:
    """
    Automated conflict detection between Market Regimes, Risk Metrics, and User Limits.
    Returns structured feedback if a hard violation is found.
    """
    
    # 1. Check Beta Alignment (Risk vs. Profile)
    actual_beta = risk.get("metrics", {}).get("beta", 0.0)
    max_allowed_beta = profile.get("max_beta", 1.2)
    
    if actual_beta > max_allowed_beta:
        return {
            "violation_type": "Concentration/Beta Risk",
            "offending_tickers": [], # LLM will fill specific tickers
            "suggested_action": f"The portfolio beta ({actual_beta}) exceeds the user limit of {max_allowed_beta}. Replace high-beta assets with defensive picks."
        }

    # 2. Check Market Regime Alignment
    regime = market.get("regime", "NEUTRAL")
    if regime == "RISK_OFF" and actual_beta > 1.0:
        return {
            "violation_type": "Regime Mismatch",
            "offending_tickers": [],
            "suggested_action": "Market is in RISK_OFF mode, but the portfolio remains aggressive. Reduce exposure to volatile growth stocks."
        }

    return None

def summarize_council_findings(state: Dict[str, Any]) -> str:
    """
    Summarizes the results of all agents into a clear report for the Orchestrator LLM.
    """
    risk = state.get("risk_assessment", {})
    market = state.get("market_context", {})
    
    summary = f"""
    COUNCIL SUMMARY (Round {state.get('iteration', 0)}):
    - Market Status: {market.get('regime')} ({market.get('confidence', 0)*100}% confidence)
    - Risk Verdict: {risk.get('verdict')}
    - Risk Reasoning: {risk.get('reasoning')}
    - Key Metrics: Beta={risk.get('metrics', {}).get('beta')}, Vol={risk.get('metrics', {}).get('volatility')}
    """
    return summary