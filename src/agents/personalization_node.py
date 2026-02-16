import logging
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

# Imports from your project structure
from src.core.llm_client import get_llm_client
from src.core.state import InvestmentState
from src.utils.personalization_tools import (
    calculate_investable_amount,
    suggest_allocation_strategy,
    validate_allocation,
    allocate_equal_weight
)

logger = logging.getLogger("PersonalizationNode")

async def personalization_node(state: InvestmentState) -> InvestmentState:
    """
    Agent: Personalization Node.
    Uses ReAct reasoning to determine ₹ allocations.
    """
    logger.info("--- NODE: Personalization (Agentic) ---")
    
    profile = state.get("user_profile")
    recs = state.get("scout_recommendations", [])
    
    # Early exit if no assets were recommended by the Scout
    if not recs:
        logger.warning("No recommendations found to personalize.")
        state["final_portfolio"] = []
        state["agent_outputs"]["personalization"] = {"error": "No recommendations provided"}
        return state

    # 1. Initialize the AI Agent with Tools
    llm_client = get_llm_client()
    tools = [
        calculate_investable_amount, 
        suggest_allocation_strategy, 
        validate_allocation, 
        allocate_equal_weight
    ]
    
    system_prompt = """You are the Portfolio Personalization Agent.
    Your goal is to allocate a user's monthly surplus across recommended assets.
    
    YOUR WORKFLOW:
    1. Calculate the 'investable_amount' using the user's monthly surplus.
    2. Request an allocation strategy based on the user's risk score.
    3. Generate the specific ₹ amounts and VALIDATE them.
    4. If validation fails (e.g., exceeds single asset limits), adjust or use 'allocate_equal_weight'.
    
    FINAL OUTPUT:
    You must provide the final portfolio in a JSON format containing a list of assets.
    """

    # 2. Create the ReAct Loop
    # We use 'prompt' or 'state_modifier' depending on your LangGraph version
    agent = create_react_agent(llm_client.gemini, tools, state_modifier=system_prompt)

    # 3. Invoke Agent
    input_msg = {
        "messages": [
            HumanMessage(content=f"Personalize this portfolio: {json.dumps(recs)} for a user with profile: {json.dumps(profile)}")
        ]
    }

    try:
        result = await agent.ainvoke(input_msg)
        final_answer = result["messages"][-1].content
        
        # Parse JSON output from the LLM
        clean_json = final_answer.replace("```json", "").replace("```", "").strip()
        portfolio_data = json.loads(clean_json)
        
        # Normalize the result to a list of assets
        final_list = portfolio_data if isinstance(portfolio_data, list) else portfolio_data.get("portfolio", [])

    except Exception as e:
        logger.error(f"Personalization Agent reasoning failed: {e}")
        # Fallback: Maintain system integrity with basic math if AI fails
        invest_data = calculate_investable_amount(
            profile.get("monthly_surplus", 0), 
            profile.get("liquidity_required_pct", 20)
        )
        final_list = allocate_equal_weight(
            recs, 
            invest_data["investable_amount"], 
            profile.get("max_single_asset_pct", 15)
        )

    # 4. Update Global State
    state["final_portfolio"] = final_list
    state["agent_outputs"]["personalization"] = {
        "messages": result["messages"] if 'result' in locals() else [],
        "verdict": "COMPLETE"
    }
    
    return state