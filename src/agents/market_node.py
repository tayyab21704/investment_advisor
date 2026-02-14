import logging
import json
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.market_data import fetch_nifty_data, fetch_vix
from langchain_core.messages import HumanMessage, BaseMessage
from typing import List

logger = logging.getLogger("MarketNode")

async def market_node(state: InvestmentState) -> InvestmentState:
    """
    Node: Market Intelligence.
    Uses a ReAct pattern to determine market regime.
    """
    logger.info("--- NODE: Market ---")
    llm = get_llm_client()
    reasoning_trace = []
    
    # --- STEP 1: THOUGHT ---
    thought1 = "To determine the market regime, I first need to check the current volatility (VIX) and the short-term trend of the benchmark index (Nifty 50)."
    reasoning_trace.append({"step": 1, "type": "THOUGHT", "content": thought1})
    
    # --- STEP 2: ACTION ---
    vix = fetch_vix()
    nifty = fetch_nifty_data()
    action1 = f"Called fetch_vix() -> {vix}; Called fetch_nifty_data() -> {nifty['trend']} (Price: {nifty['price']})"
    reasoning_trace.append({"step": 2, "type": "ACTION", "content": action1})
    
    # --- STEP 3: OBSERVATION ---
    observation1 = f"Current Market State: VIX is {vix}. Nifty 50 trend is {nifty['trend']} with a 1-month change of {nifty['change_1mo_pct']}%."
    reasoning_trace.append({"step": 3, "type": "OBSERVATION", "content": observation1})
    
    # --- STEP 4: THOUGHT (LLM Guided) ---
    prompt2 = f"""
    You are a Market Intelligence Agent.
    Based on these observations:
    - VIX: {vix}
    - Nifty Trend: {nifty['trend']} ({nifty['change_1mo_pct']}%)
    
    Current Reasoning Trace: {json.dumps(reasoning_trace)}
    
    Task:
    1. Provide a 'Thought' on how these indicators suggest a specific market regime (RISK_ON, RISK_OFF, or NEUTRAL).
    2. Provide a final 'Action' which is the classification and a brief rationale.
    
    Return ONLY JSON:
    {{
      "thought": "your analytical thought",
      "regime": "RISK_ON" | "RISK_OFF" | "NEUTRAL",
      "rationale": "short summary"
    }}
    """
    
    try:
        response = await llm.invoke([HumanMessage(content=prompt2)])
        res_json = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        
        reasoning_trace.append({"step": 4, "type": "THOUGHT", "content": res_json["thought"]})
        reasoning_trace.append({"step": 5, "type": "ACTION", "content": f"Classified regime as {res_json['regime']}"})
        
        market_context = {
            "regime": res_json["regime"],
            "vix": vix,
            "nifty_trend": nifty["trend"],
            "rationale": res_json["rationale"]
        }
    except Exception as e:
        logger.error(f"Error in Market ReAct loop: {e}")
        market_context = {"regime": "NEUTRAL", "vix": vix, "nifty_trend": "NEUTRAL", "rationale": "Fallback due to LLM error."}

    # Store in state
    state["market_context"] = market_context
    state["agent_outputs"]["market"] = {
        "verdict": market_context["regime"],
        "reasoning_trace": reasoning_trace,
        "metrics": {"vix": vix, "nifty": nifty}
    }
    
    return state
