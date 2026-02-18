import logging
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.personalization_tools import (
    calculate_investable_amount,
    validate_allocation,
    suggest_allocation_strategy,
    allocate_equal_weight
)

logger = logging.getLogger("PersonalizationNode")

tools = [calculate_investable_amount, validate_allocation, suggest_allocation_strategy, allocate_equal_weight]
tool_map = {
    "calculate_investable_amount": calculate_investable_amount,
    "validate_allocation": validate_allocation,
    "suggest_allocation_strategy": suggest_allocation_strategy,
    "allocate_equal_weight": allocate_equal_weight
}

async def personalization_node(state: InvestmentState) -> InvestmentState:
    """
    Portfolio Allocation Agent:
    Fixed: Async ainvoke implementation and high-quality fallback logic restored.
    """
    logger.info("💰 Personalization Agent: Starting allocation...")
    
    recommendations = state.get("scout_recommendations", [])
    profile = state["user_profile"]
    
    if not recommendations:
        state["final_portfolio"] = []
        return state
    
    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    sys_msg = SystemMessage(content=f"""
        You are a Financial Planner. Allocate ₹{profile['monthly_surplus']} across assets.
        Risk Score: {profile['actual_risk_capacity']}/10. 
        Liquidity Reserve: {profile['liquidity_required_pct']}%.
        Respect max_per_asset: {profile['max_single_asset_pct']}%.
    """)
    
    messages = [sys_msg, HumanMessage(content="Allocate the portfolio using tools.")]
    
    loop_active, iteration, final_output = True, 0, {}
    
    while loop_active and iteration < 6:
        # FIX: Changed .invoke to .ainvoke
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)
        iteration += 1
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                if fn_name == "none": continue
                
                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**tool_call["args"])
                        messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"]))
                    except Exception as e:
                        messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call["id"]))
        else:
            try:
                clean_content = response.content.replace("```json", "").replace("```", "").strip()
                final_output = json.loads(clean_content)
                loop_active = False
                logger.info(f"✅ Allocation complete: {len(final_output.get('portfolio', []))} assets")
            except Exception:
                messages.append(HumanMessage(content="Provide final allocation in valid JSON format."))

    # High-quality fallback if AI fails to converge
    if not final_output or "portfolio" not in final_output:
        logger.warning("Agent failed to converge. Using equal-weight fallback.")
        calc_result = calculate_investable_amount(profile["monthly_surplus"], profile["liquidity_required_pct"])
        fallback_portfolio = allocate_equal_weight(recommendations, calc_result["investable_amount"], profile["max_single_asset_pct"])
        final_output = {"portfolio": fallback_portfolio}

    state["final_portfolio"] = final_output.get("portfolio", [])
    state["agent_outputs"]["personalization"] = {"steps": iteration, "trace": messages}
    return state