import logging
import json
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.market_data import fetch_market_indicators, fetch_sectoral_breadth

logger = logging.getLogger("MarketNode")

# 1. Define the Toolkit
# We wrap your utils so the LLM can understand them as "Tools"
tools = [fetch_market_indicators, fetch_sectoral_breadth]

# Map functions for execution
tool_map = {
    "fetch_market_indicators": fetch_market_indicators,
    "fetch_sectoral_breadth": fetch_sectoral_breadth
}

async def market_node(state: InvestmentState) -> InvestmentState:
    """
    True Autonomous Market Agent.
    Uses Native Function Calling to investigate the market and decide the regime.
    """
    logger.info("🌍 Market Agent: specific tools bound. Starting Autonomous Loop...")
    
    # 1. Initialize LLM with Tools Bound
    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    # 2. Define the Agent's Goal (System Prompt)
    sys_msg = SystemMessage(content="""
        You are a Senior Market Strategist. Your goal is to determine the current 'Market Regime'.
        
        Regime Definitions:
        - RISK_ON: Low Volatility (VIX < 18), Bullish Trend, Broad Participation.
        - RISK_OFF: High Volatility (VIX > 22) OR Bearish Trend.
        - NEUTRAL: Mixed signals.

        You have access to tools to fetch real-time data. 
        USE THEM. Do not guess. 
        Once you have enough data, output the final regime and a confidence score (0.0-1.0).
        
        Final Answer Format (JSON):
        {
            "regime": "RISK_ON",
            "confidence": 0.9,
            "reasoning": "VIX is low and sectors are green."
        }
    """)
    
    # 3. The Conversation History (Internal Memory)
    messages = [sys_msg, HumanMessage(content="Analyze the current market conditions and determine the regime.")]
    
    # 4. The Autonomous ReAct Loop
    loop_active = True
    iteration_count = 0
    final_output = {}
    
    while loop_active and iteration_count < 5:
        # Ask LLM for next move
        response = await llm_with_tools.invoke(messages)
        messages.append(response) # Add AI response to history
        iteration_count += 1
        
        # CHECK: Did the LLM call a tool?
        if response.tool_calls:
            logger.info(f"🛠️ Agent decided to call: {len(response.tool_calls)} tools")
            
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                args = tool_call["args"]
                
                # Execute the tool
                if fn_name in tool_map:
                    try:
                        logger.info(f"   -> Executing {fn_name}...")
                        result = tool_map[fn_name](**args)
                        content = json.dumps(result)
                    except Exception as e:
                        content = f"Error executing {fn_name}: {str(e)}"
                else:
                    content = "Error: Tool not found."
                
                # Feed observation back to LLM
                tool_msg = ToolMessage(content=content, tool_call_id=tool_call["id"])
                messages.append(tool_msg)
                
        # CHECK: Did the LLM provide a final answer?
        else:
            # No tool calls means it has an answer
            raw_content = response.content
            try:
                # Attempt to parse JSON from the final response
                clean_content = raw_content.replace("```json", "").replace("```", "").strip()
                final_output = json.loads(clean_content)
                loop_active = False # Break the loop
                logger.info(f"✅ Agent reached conclusion: {final_output.get('regime')}")
            except Exception:
                # If LLM didn't output JSON, nudge it
                logger.warning("Agent did not output valid JSON. Nudging...")
                messages.append(HumanMessage(content="Please provide your final answer strictly in the requested JSON format."))

    # 5. Fallback if loop exhausts
    if not final_output:
        final_output = {"regime": "NEUTRAL", "confidence": 0.5, "reasoning": "Agent failed to converge."}

    # 6. Update State
    state["market_context"] = {
        "regime": final_output.get("regime", "NEUTRAL"),
        "confidence": final_output.get("confidence", 0.5),
        "raw_analysis": final_output.get("reasoning", "")
    }
    
    # Save the trace so we can see what the agent did
    state["agent_outputs"]["market"] = {
        "messages": messages, 
        "verdict": final_output.get("regime")
    }

    return state