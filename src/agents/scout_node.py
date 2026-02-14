import logging
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.scout_tools import get_universe_by_regime, analyze_ticker, get_vibe_check

logger = logging.getLogger("ScoutNode")

# 1. Define Tools
tools = [get_universe_by_regime, analyze_ticker, get_vibe_check]

tool_map = {
    "get_universe_by_regime": get_universe_by_regime,
    "analyze_ticker": analyze_ticker,
    "get_vibe_check": get_vibe_check
}

async def scout_node(state: InvestmentState) -> InvestmentState:
    """
    True Autonomous Scout Agent.
    It receives a mission and decides how to execute the search.
    """
    logger.info(f"🔍 Scout Agent: Autonomous Mode (Cycle {state.get('iteration', 0)})")
    
    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    # Context
    profile = state["user_profile"]
    market = state["market_context"]
    is_revision = state.get("iteration", 0) > 0
    feedback = state.get("orchestrator_decision", {}).get("reasoning", "") if is_revision else ""

    # 2. System Prompt (The Mission)
    sys_msg = SystemMessage(content=f"""
        You are an elite Stock Scout.
        
        GOAL: Find 5-7 best assets for a user with Risk Capacity: {profile['actual_risk_capacity']}/10.
        MARKET CONTEXT: The market is currently {market['regime']}.
        
        TOOLS:
        - `get_universe_by_regime(regime)`: Get a list of potential tickers.
        - `analyze_ticker(ticker)`: Get fundamentals and a Quality Score (0-100).
        - `get_vibe_check(ticker)`: Get news sentiment.
        
        INSTRUCTIONS:
        1. Start by fetching the universe for the current regime.
        2. Analyze the fundamentals of the most promising candidates.
        3. Check sentiment (vibe) for your top picks.
        4. {f'IMPORTANT: This is a REVISION. Previous feedback: "{feedback}". Adjust accordingly.' if is_revision else ''}
        
        Output the final portfolio in JSON format containing a list of objects with 'ticker', 'name', 'reasoning'.
    """)
    
    messages = [sys_msg, HumanMessage(content="Begin your search.")]
    
    # 3. Autonomous Loop
    loop_active = True
    iteration_count = 0
    final_picks = []
    
    while loop_active and iteration_count < 8: # Scout needs more steps
        response = await llm_with_tools.invoke(messages)
        messages.append(response)
        iteration_count += 1
        
        if response.tool_calls:
            logger.info(f"🛠️ Scout calling {len(response.tool_calls)} tools...")
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                args = tool_call["args"]
                
                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**args)
                        content = json.dumps(result)
                    except Exception as e:
                        content = f"Error: {str(e)}"
                else:
                    content = "Tool not found"
                
                messages.append(ToolMessage(content=content, tool_call_id=tool_call["id"]))
        else:
            # Process Final Answer
            try:
                content = response.content.replace("```json", "").replace("```", "").strip()
                data = json.loads(content)
                final_picks = data.get("portfolio", data) if isinstance(data, dict) else data
                loop_active = False
                logger.info(f"✅ Scout finished. Found {len(final_picks)} assets.")
            except Exception:
                messages.append(HumanMessage(content="Please provide the FINAL portfolio as valid JSON."))

    # 4. Update State
    if not final_picks:
        logger.error("Scout failed to produce a portfolio.")
        final_picks = [] # Or handle fallback

    state["scout_recommendations"] = final_picks
    state["agent_outputs"]["scout"] = {
        "steps": iteration_count,
        "trace": messages # Save full objects
    }
    
    return state