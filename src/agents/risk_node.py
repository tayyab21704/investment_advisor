import logging
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.risk_tools import get_comprehensive_risk_metrics, analyze_diversification, run_stress_test

logger = logging.getLogger("RiskNode")

# Define the Toolkit
tools = [get_comprehensive_risk_metrics, analyze_diversification, run_stress_test]

tool_map = {
    "get_comprehensive_risk_metrics": get_comprehensive_risk_metrics,
    "analyze_diversification": analyze_diversification,
    "run_stress_test": run_stress_test
}

async def risk_node(state: InvestmentState) -> InvestmentState:
    """
    Risk Guardian Agent:
    Audits the Scout's recommendations against the User's Risk Profile.
    Can REJECT the portfolio, triggering a feedback loop.
    """
    logger.info("🛡️ Risk Guardian: Starting Audit...")
    
    # 1. Extract Context
    scout_output = state.get("scout_recommendations", [])
    user_risk_score = state["user_profile"]["actual_risk_capacity"] # 1-10 scale
    
    # Extract tickers list
    tickers = [item['ticker'] for item in scout_output if 'ticker' in item]
    
    if not tickers:
        logger.warning("Risk Agent received empty portfolio. Skipping.")
        return state

    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    # 2. The System Prompt (The Rulebook)
    sys_msg = SystemMessage(content=f"""
        You are the Chief Risk Officer (CRO) of an investment firm.
        
        YOUR GOAL: Audit a proposed portfolio for a user with Risk Capacity: {user_risk_score}/10.
        
        RISK LIMITS (Strict Enforcement):
        - Conservative (1-4): Max Beta 0.8, Max Drawdown 15%.
        - Moderate (5-7): Max Beta 1.1, Max Drawdown 25%.
        - Aggressive (8-10): Max Beta 1.5, Max Drawdown 40%.
        
        YOUR TOOLS:
        1. `get_comprehensive_risk_metrics(tickers)`: Get Beta, Volatility, VaR.
        2. `analyze_diversification(tickers)`: Check if assets are too correlated.
        3. `run_stress_test(tickers)`: Simulate a 20% market crash.
        
        INSTRUCTIONS:
        1. RUN THE NUMBERS. Call the tools to get the hard data.
        2. COMPARE against the Risk Limits above.
        3. ISSUE VERDICT:
            - If safe: Output "APPROVE".
            - If unsafe: Output "REJECT".
        
        FINAL OUTPUT FORMAT (JSON):
        {{
            "verdict": "APPROVE" | "REJECT",
            "metrics": {{ "beta": 1.2, "max_drawdown": 22.5, "stress_test_loss": -24.0 }},
            "reasoning": "Beta of 1.2 exceeds limit of 0.8 for conservative user.",
            "feedback": "Reduce exposure to high-beta assets like Tech/Crypto."
        }}
    """)
    
    messages = [sys_msg, HumanMessage(content=f"Audit this portfolio: {tickers}")]
    
    # 3. Autonomous ReAct Loop
    loop_active = True
    iteration = 0
    final_output = {}
    
    while loop_active and iteration < 6:
        response = await llm_with_tools.invoke(messages)
        messages.append(response)
        iteration += 1
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                args = tool_call["args"]
                
                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**args)
                        content = json.dumps(result)
                    except Exception as e:
                        content = f"Error: {str(e)}"
                        
                    messages.append(ToolMessage(content=content, tool_call_id=tool_call["id"]))
        else:
            # Parse Final Verdict
            try:
                text = response.content.replace("```json", "").replace("```", "").strip()
                final_output = json.loads(text)
                loop_active = False
            except Exception:
                messages.append(HumanMessage(content="Output valid JSON only."))

    # 4. Update State & Feedback Loop Logic
    state["risk_assessment"] = final_output
    
    # Save trace for debugging
    state["agent_outputs"]["risk"] = {
        "messages": messages, # Save full objects for tracing
        "verdict": final_output.get("verdict", "REJECT")
    }
    
    # LOGIC FOR THE GRAPH:
    # If Rejected, we flag it so the Graph knows to loop back.
    if final_output.get("verdict") == "REJECT":
        logger.info(f"❌ REJECTED: {final_output.get('reasoning')}")
        # We assume the Graph will handle the loop-back, 
        # but we mark the decision clearly here.
        state["decision"] = "REJECT" 
    else:
        logger.info("✅ APPROVED: Portfolio passed audit.")
        state["decision"] = "APPROVE"

    return state