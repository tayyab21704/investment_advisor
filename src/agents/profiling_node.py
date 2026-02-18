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

# Define Tools
tools = [
    calculate_investable_amount,
    validate_allocation,
    suggest_allocation_strategy,
    allocate_equal_weight
]

tool_map = {
    "calculate_investable_amount": calculate_investable_amount,
    "validate_allocation": validate_allocation,
    "suggest_allocation_strategy": suggest_allocation_strategy,
    "allocate_equal_weight": allocate_equal_weight
}

async def personalization_node(state: InvestmentState) -> InvestmentState:
    """
    Portfolio Allocation Agent:
    Converts Scout's asset recommendations into monthly ₹ investments.
    Uses tools to calculate, validate, and optimize allocations.
    """
    logger.info("💰 Personalization Agent: Starting allocation...")
    
    # Extract context from state
    recommendations = state.get("scout_recommendations", [])
    profile = state["user_profile"]
    
    if not recommendations:
        logger.error("No recommendations from Scout. Cannot allocate.")
        state["final_portfolio"] = []
        state["agent_outputs"]["personalization"] = {
            "error": "No assets to allocate"
        }
        return state
    
    # Extract user constraints
    monthly_surplus = profile["monthly_surplus"]
    liquidity_pct = profile["liquidity_required_pct"]
    max_per_asset = profile["max_single_asset_pct"]
    risk_score = profile["actual_risk_capacity"]
    
    # Initialize LLM with tools
    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    # System Prompt (The Mission)
    sys_msg = SystemMessage(content=f"""
You are a Certified Financial Planner (CFP) specializing in portfolio allocation.

YOUR GOAL: Convert Scout's asset picks into monthly investment amounts (₹).

USER PROFILE:
- Monthly Surplus: ₹{monthly_surplus}
- Risk Capacity: {risk_score}/10
- Liquidity Requirement: {liquidity_pct}%
- Max Per Asset: {max_per_asset}%

ASSETS FROM SCOUT:
{json.dumps(recommendations, indent=2)}

YOUR TOOLS:
1. `calculate_investable_amount(monthly_surplus, liquidity_pct)`
2. `suggest_allocation_strategy(risk_score, asset_types)`
3. `validate_allocation(allocations, investable_amount, max_per_asset)`
4. `allocate_equal_weight(assets, investable_amount, max_per_asset)`

FINAL OUTPUT (JSON):
{{
    "portfolio": [
        {{
            "ticker": "TCS.NS",
            "name": "Tata Consultancy Services",
            "monthly_investment": 3200,
            "allocation_pct": 20.0,
            "type": "equity",
            "reasoning": "..."
        }}
    ],
    "summary": {{ ... }}
}}
""")
    
    messages = [sys_msg, HumanMessage(content="Allocate the portfolio using the tools available.")]
    
    loop_active = True
    iteration = 0
    final_output = {}
    
    while loop_active and iteration < 6:
        # Preserving your use of ainvoke
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)
        iteration += 1
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                
                # NEW: Hallucination filter for Groq
                if fn_name == "none":
                    logger.info("Ignoring 'none' tool hallucination.")
                    continue
                
                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**tool_call["args"])
                        messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"]))
                    except Exception as e:
                        messages.append(ToolMessage(content=f"Error: {str(e)}", tool_call_id=tool_call["id"]))
                else:
                    messages.append(ToolMessage(content="Error: Tool not found.", tool_call_id=tool_call["id"]))
        else:
            try:
                raw_content = response.content
                clean_content = raw_content.replace("```json", "").replace("```", "").strip()
                final_output = json.loads(clean_content)
                loop_active = False
            except Exception:
                messages.append(HumanMessage(content="Please provide your final allocation in valid JSON format only."))
    
    # Fallback if loop exhausts
    if not final_output or "portfolio" not in final_output:
        logger.warning("Agent failed to converge. Using equal-weight fallback.")
        calc_result = calculate_investable_amount(monthly_surplus, liquidity_pct)
        fallback_portfolio = allocate_equal_weight(recommendations, calc_result["investable_amount"], max_per_asset)
        final_output = {"portfolio": fallback_portfolio}
    
    # Update State
    state["final_portfolio"] = final_output.get("portfolio", [])
    state["agent_outputs"]["personalization"] = {
        "steps": iteration,
        "trace": messages,
        "verdict": "APPROVE" 
    }
    
    return state