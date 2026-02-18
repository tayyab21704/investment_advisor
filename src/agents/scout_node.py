import logging
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.scout_tools import (
    get_universe_by_regime, 
    get_real_time_fundamentals, 
    find_safe_fallback_assets
)

logger = logging.getLogger("ScoutNode")

# Define tools
tools = [get_universe_by_regime, get_real_time_fundamentals, find_safe_fallback_assets]
tool_map = {
    "get_universe_by_regime": get_universe_by_regime,
    "get_real_time_fundamentals": get_real_time_fundamentals,
    "find_safe_fallback_assets": find_safe_fallback_assets
}

async def scout_node(state: InvestmentState) -> InvestmentState:
    """
    Scout Agent: The 'Idea Generator'.
    LEARNING CAPABILITY: Reads feedback from previous rounds to refine search.
    """
    iteration = state.get("iteration", 0)
    feedback = state.get("feedback_for_scout", {})
    
    logger.info(f"🔍 Scout Agent: Cycle {iteration}")
    if feedback:
        logger.info(f"   ⚠️ ADAPTING STRATEGY based on feedback: {json.dumps(feedback)}")

    # 1. Get User Profile & Market Context
    profile = state["user_profile"]
    market = state["market_context"]
    
    # 2. Construct Dynamic Prompt based on Iteration
    base_prompt = f"""
    You are an Equities Scout. Find best stocks for:
    - Risk Capacity: {profile.get('actual_risk_capacity', 5)}/10
    - Market Regime: {market.get('regime', 'NEUTRAL')}
    """

    # If this is a retry (iteration > 0), inject the feedback Lesson
    if iteration > 0 and feedback:
        base_prompt += f"""
        \n🚨 CRITICAL FEEDBACK FROM PREVIOUS ROUND:
        The Risk Officer REJECTED your last picks.
        Reason: {feedback.get('reasoning', 'Unknown')}
        Violation Type: {feedback.get('violation_type', 'General Risk')}
        
        YOUR NEW MISSION:
        1. You MUST filter for safer assets.
        2. Use `get_real_time_fundamentals` to CHECK Beta and Volatility.
        3. If feedback says "High Beta", ensure your new picks have Beta < 1.0.
        """
    else:
        base_prompt += "\nSelect 3-5 high-quality Indian stocks (NSE). Use `get_universe_by_regime` to start."

    sys_msg = SystemMessage(content=base_prompt + "\nReturn JSON: [{'ticker': '...', 'name': '...', 'reason': '...'}]")
    
    # 3. Initialize LLM
    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    messages = [sys_msg, HumanMessage(content="Begin search.")]
    
    # 4. ReAct Loop
    loop_active = True
    loop_count = 0
    final_recs = []
    
    while loop_active and loop_count < 6:
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)
        loop_count += 1
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                
                # Hallucination check for Groq
                if fn_name == "none": 
                    continue 
                
                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**tool_call["args"])
                        messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"]))
                    except Exception as e:
                        messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call["id"]))
        else:
            try:
                # Parse JSON output
                content = response.content.replace("```json", "").replace("```", "").strip()
                # Find JSON array
                start = content.find('[')
                end = content.rfind(']')
                if start != -1 and end != -1:
                    final_recs = json.loads(content[start:end+1])
                    loop_active = False
            except Exception:
                messages.append(HumanMessage(content="Provide strictly a JSON list of assets."))

    # 5. Fallback: If Scout fails to find stocks, use Safe ETFs
    if not final_recs:
        logger.warning("Scout failed to find stocks. Deploying Safe Fallback Assets.")
        final_recs = find_safe_fallback_assets()

    state["scout_recommendations"] = final_recs
    return state