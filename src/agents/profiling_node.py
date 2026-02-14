import logging
import json
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.database.mongo_client import get_mongo_client
from src.utils.behavioral_profiling import calculate_behavioral_risk_score
from langchain_core.messages import HumanMessage

logger = logging.getLogger("ProfilingNode")

async def profiling_node(state: InvestmentState) -> InvestmentState:
    """
    Node: Profiling.
    Combines financial data (from DB) with behavioral answers (from state)
    to establish the 'actual_risk_capacity'.
    """
    logger.info("--- NODE: Profiling ---")
    user_id = state.get("user_id")
    behavioral_answers = state.get("behavioral_answers", [])
    
    # 1. Fetch User Data from DB
    mongo = get_mongo_client()
    db_user = mongo.get_user_by_id(user_id)
    financial_risk_score = db_user.get("risk_score", 5)
    
    # 2. Calculate Behavioral Risk Score
    behavioral_risk_score = calculate_behavioral_risk_score(behavioral_answers)
    
    # 3. Derive Conservative Risk Capacity
    actual_risk = min(financial_risk_score, behavioral_risk_score)
    mismatch_warning = abs(financial_risk_score - behavioral_risk_score) > 3
    
    # 4. Use LLM to derive financial parameters based on actual_risk
    llm = get_llm_client()
    prompt = f"""
    Analyze this investor profile and derive exact financial constraints:
    - Actual Risk Capacity: {actual_risk}/10 (1=Ultra-Safe, 10=Aggressive)
    - Monthly Income: ₹{db_user.get('income', 0)}
    - Monthly Surplus: ₹{db_user.get('monthly_surplus', 0)}
    - Behavioral Mismatch Warning: {mismatch_warning}

    Return ONLY a JSON object with:
    {{
      "max_drawdown_pct": int,
      "max_single_asset_pct": int,
      "max_high_risk_allocation_pct": int,
      "liquidity_required_pct": int (reserve for emergencies),
      "investment_horizon_years": int,
      "human_conclusion": [list of 3 key profile observations]
    }}
    """
    
    try:
        response = await llm.invoke([HumanMessage(content=prompt)])
        raw_content = response.content
        # Simple JSON extraction
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
        
        derived_params = json.loads(raw_content)
    except Exception as e:
        logger.error(f"Error in profiling LLM call: {e}")
        derived_params = {
            "max_drawdown_pct": 15,
            "max_single_asset_pct": 20,
            "max_high_risk_allocation_pct": 10,
            "liquidity_required_pct": 20,
            "investment_horizon_years": 3,
            "human_conclusion": ["Safe defaults used due to parsing error."]
        }

    # 5. Populate Profile in State
    profile = {
        "user_id": user_id,
        "financial_risk_score": financial_risk_score,
        "behavioral_risk_score": behavioral_risk_score,
        "actual_risk_capacity": actual_risk,
        "mismatch_warning": mismatch_warning,
        "income": db_user.get('income', 0),
        "monthly_surplus": db_user.get('monthly_surplus', 0),
        **derived_params
    }
    
    state["user_profile"] = profile
    state["agent_outputs"]["profiling"] = {
        "verdict": "COMPLETE",
        "risk_capacity": actual_risk,
        "observations": profile.get("human_conclusion", [])
    }
    
    return state
