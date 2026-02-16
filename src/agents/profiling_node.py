import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

# Local Imports
from src.utils.profiling_utils import (
    analyze_loss_aversion, 
    analyze_income_stability, 
    calculate_final_risk_score
)
from src.core.llm_client import get_llm_client
from src.core.state import InvestmentState

logger = logging.getLogger("ProfilingNode")

async def profiling_node(state: InvestmentState) -> InvestmentState:
    """
    The Profiling Agent: Determines the user's risk capacity (1-10) using ReAct.
    It synthesizes financial health and behavioral signals into a single score.
    """
    logger.info("👤 Profiling Agent: Starting risk analysis...")

    # 1. Access Input Data
    # raw_user_data is assumed to be populated by the entry point or DB fetch
    user_data = state.get("raw_user_data")
    
    if not user_data:
        logger.error("Profiling failed: No raw_user_data found in state.")
        state["user_profile"] = {"actual_risk_capacity": 5, "error": "Missing input"}
        return state

    # 2. Agent Setup
    llm = get_llm_client()
    
    # We use the specific behavioral and financial functions as tools
    tools = [analyze_loss_aversion, analyze_income_stability, calculate_final_risk_score]

    # The System Prompt defines the Agent's decision-making logic
    system_prompt = """You are the Profiling Agent. Your mission is to calculate a user's 
    ACTUAL risk capacity (1-10).
    
    OPERATIONAL RULES:
    1. YOU MUST USE TOOLS: Start with 'analyze_loss_aversion' and 'analyze_income_stability'.
    2. LOGIC OVERRIDE: Behavioral panic signals (detected by tools) MUST reduce 
       the final risk score, regardless of demographic data like age or income.
    3. FINAL MATH: Always use 'calculate_final_risk_score' for the definitive integer.
    
    RESPONSE FORMAT:
    Return your final answer strictly as a JSON object:
    {
        "actual_risk_capacity": <int>,
        "risk_appetite": "Conservative" | "Moderate" | "Aggressive",
        "behavioral_flags": ["panic_seller", "etc"],
        "reasoning": "A concise explanation for the score."
    }
    """

    # Create the ReAct agent runnable using the primary Gemini model
    agent_runnable = create_react_agent(llm.gemini, tools, prompt=system_prompt)

    # 3. Execution Phase
    agent_input = {
        "messages": [
            HumanMessage(content=f"Analyze risk for this user data: {json.dumps(user_data)}")
        ]
    }

    try:
        # Run the autonomous ReAct loop
        result = await agent_runnable.ainvoke(agent_input)
        
        # Extract the final concluding message from the conversation history
        final_response = result["messages"][-1].content
        
        # 4. Structured Output Extraction
        # Cleaning potential markdown formatting (```json) from LLM output
        clean_json = final_response.replace("```json", "").replace("```", "").strip()
        profile_dict = json.loads(clean_json)
        
        logger.info(f"✅ Profiling Complete. Final Risk Score: {profile_dict.get('actual_risk_capacity')}")

    except Exception as e:
        logger.error(f"Error in Profiling Agent execution: {str(e)}")
        # Defensive Fallback: Use a neutral safety score if reasoning fails
        profile_dict = {
            "actual_risk_capacity": 5, 
            "risk_appetite": "Moderate", 
            "reasoning": "System error; applied default risk profile."
        }

    # 5. State Update
    # Updating the user_profile so subsequent nodes (Scout/Risk) can read it
    state["user_profile"] = profile_dict
    
    return state