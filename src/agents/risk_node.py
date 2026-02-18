import logging
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from src.utils.risk_tools import get_comprehensive_risk_metrics, analyze_diversification, run_stress_test

logger = logging.getLogger("RiskNode")

tools = [get_comprehensive_risk_metrics, analyze_diversification, run_stress_test]
tool_map = {
    "get_comprehensive_risk_metrics": get_comprehensive_risk_metrics,
    "analyze_diversification": analyze_diversification,
    "run_stress_test": run_stress_test
}

async def risk_node(state: InvestmentState) -> InvestmentState:
    """Risk Guardian: Audits portfolio. Includes Groq 'none' filter and robust fallbacks."""
    logger.info("🛡️ Risk Guardian: Starting Audit...")
    
    scout_output = state.get("scout_recommendations", [])
    user_risk_score = state["user_profile"]["actual_risk_capacity"]
    tickers = [item['ticker'] for item in scout_output if 'ticker' in item]
    
    if not tickers:
        state["decision"] = "REJECT"
        return state

    llm = get_llm_client()
    llm_with_tools = llm.bind_tools(tools)
    
    sys_msg = SystemMessage(content=f"""
        You are the CRO. Audit for Risk Score {user_risk_score}/10.
        Call tools. Compare limits.
        Return JSON with 'verdict' ("Approved" or "Rejected") and 'reasoning'.
        IMPORTANT: Do NOT hallucinate a tool named 'none'.
    """)
    
    messages = [sys_msg, HumanMessage(content=f"Audit: {tickers}")]
    loop_active, iteration = True, 0
    final_output = {} # Default empty
    
    while loop_active and iteration < 6:
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)
        iteration += 1
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                
                if fn_name == "none": # Groq Hallucination Filter
                    continue 
                
                if fn_name in tool_map:
                    try:
                        result = tool_map[fn_name](**tool_call["args"])
                        messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"]))
                    except Exception as e:
                        messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call["id"]))
        else:
            try:
                # Attempt Smart Parse logic here too
                content = response.content
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    final_output = json.loads(content[start:end+1])
                    loop_active = False
            except Exception:
                messages.append(HumanMessage(content="Output valid JSON only."))

    # Validating the output
    state["risk_assessment"] = final_output
    
    # Robust decision mapping
    verdict = final_output.get("verdict", "").lower()
    if "approv" in verdict: # Catch 'approve', 'approved', 'approves'
        state["decision"] = "APPROVE"
        logger.info("✅ Risk Audit Passed.")
    else:
        state["decision"] = "REJECT"
        reason = final_output.get("reasoning", "No reasoning provided.")
        logger.info(f"❌ Risk Audit Failed: {reason}")

    state["agent_outputs"]["risk"] = {"verdict": state["decision"]}
    return state