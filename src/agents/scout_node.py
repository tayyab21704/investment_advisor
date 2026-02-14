import logging
import json
from typing import List, Dict
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.market_data import screen_nifty_50, fetch_stock_info
from langchain_core.messages import HumanMessage

logger = logging.getLogger("ScoutNode")

async def scout_node(state: InvestmentState) -> InvestmentState:
    """
    Node: Scout.
    Multi-Step ReAct pattern for investment discovery and ranking.
    """
    logger.info("--- NODE: Scout ---")
    llm = get_llm_client()
    profile = state["user_profile"]
    market = state["market_context"]
    reasoning_trace = []

    # --- REACT CYCLE 1: CRITERIA DERIVATION ---
    thought1 = f"The user has a risk capacity of {profile['actual_risk_capacity']}/10 and the market is in a {market['regime']} regime. I need to define specific screening criteria for quality and sector allocation."
    reasoning_trace.append({"step": 1, "type": "THOUGHT", "content": thought1})
    
    criteria = {
        "min_quality_score": 7 if profile['actual_risk_capacity'] > 5 else 8,
        "market_regime": market['regime']
    }
    action1 = f"Defined screening criteria: {criteria}"
    reasoning_trace.append({"step": 2, "type": "ACTION", "content": action1})
    
    observation1 = "Criteria defined for screening Nifty 50 universe."
    reasoning_trace.append({"step": 3, "type": "OBSERVATION", "content": observation1})

    # --- REACT CYCLE 2: SCREENING ---
    thought2 = "Now I will screen the Nifty 50 universe to find candidates that match the quality profile."
    reasoning_trace.append({"step": 4, "type": "THOUGHT", "content": thought2})
    
    candidates = screen_nifty_50(criteria)
    action2 = f"Called screen_nifty_50() -> Found {len(candidates)} candidates."
    reasoning_trace.append({"step": 5, "type": "ACTION", "content": action2})
    
    observation2 = f"Candidates found: {[c['ticker'] for c in candidates]}"
    reasoning_trace.append({"step": 6, "type": "OBSERVATION", "content": observation2})

    # --- REACT CYCLE 3: RANKING & QUALITY CHECK ---
    thought3 = "I need to rank these candidates and fetch detailed info (beta, price) to ensure they fit the risk profile."
    reasoning_trace.append({"step": 7, "type": "THOUGHT", "content": thought3})
    
    ranked_recommendations = []
    # Fetch details for top candidates
    for c in candidates[:4]:
        info = fetch_stock_info(c["ticker"])
        ranked_recommendations.append({
            "ticker": c["ticker"],
            "sector": c["sector"],
            "quality_score": c["quality_score"],
            "beta": info["beta"],
            "price": info["price"]
        })
    
    action3 = f"Fetched details and ranked top {len(ranked_recommendations)} assets."
    reasoning_trace.append({"step": 8, "type": "ACTION", "content": action3})
    
    observation3 = f"Ranked candidates with metrics: {ranked_recommendations}"
    reasoning_trace.append({"step": 9, "type": "OBSERVATION", "content": observation3})

    # --- REACT CYCLE 4: FINAL REFINEMENT (LLM Guided) ---
    prompt4 = f"""
    You are a Scout Agent in a multi-agent investment system.
    Current Findings: {json.dumps(observation3)}
    User Profile: Risk {profile['actual_risk_capacity']}/10, Max High-Risk Allocation {profile['max_high_risk_allocation_pct']}%
    
    Task:
    1. Should we add a high-growth asset (like Bitcoin) if it fits the high-risk limit?
    2. Finalize the list of exactly 3-4 recommendations.
    3. Provide a brief reasoning for the final selection.

    Return ONLY JSON:
    {{
      "thought": "your final selection thought",
      "final_recommendations": [
        {{"ticker": "TICKER", "reasoning": "why it was picked"}}
      ]
    }}
    """
    
    try:
        response = await llm.invoke([HumanMessage(content=prompt4)])
        res_json = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        
        reasoning_trace.append({"step": 10, "type": "THOUGHT", "content": res_json["thought"]})
        
        # Merge metrics back into final recommendations
        final_list = []
        for rec in res_json["final_recommendations"]:
            match = next((c for c in ranked_recommendations if c["ticker"] == rec["ticker"]), {"beta": 1.0})
            final_list.append({
                "ticker": rec["ticker"],
                "reasoning": rec["reasoning"],
                "beta": match.get("beta", 1.0)
            })
            
        action4 = f"Finalized recommendations: {[r['ticker'] for r in final_list]}"
        reasoning_trace.append({"step": 11, "type": "ACTION", "content": action4})
        
    except Exception as e:
        logger.error(f"Error in Scout ReAct loop: {e}")
        final_list = [{"ticker": "RELIANCE.NS", "reasoning": "Bluechip fallback", "beta": 0.9}]

    # Store in state
    state["scout_recommendations"] = final_list
    state["agent_outputs"]["scout"] = {
        "verdict": "COMPLETE",
        "count": len(final_list),
        "reasoning_trace": reasoning_trace,
        "recommendations": final_list
    }
    
    return state
