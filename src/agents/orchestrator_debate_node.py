import logging
import json
from src.core.state import InvestmentState
from src.core.llm_client import get_llm_client
from langchain_core.messages import HumanMessage

logger = logging.getLogger("OrchestratorDebateNode")

async def orchestrator_debate_node(state: InvestmentState) -> InvestmentState:
    """
    Node: Orchestrator Debate (Council).
    Evaluates all agent outputs for conflicts and final fit.
    """
    logger.info("--- NODE: Orchestrator Debate ---")
    llm = get_llm_client()
    
    # 1. Gather Agent Outputs
    scout_output = state["agent_outputs"].get("scout", {})
    risk_output = state["agent_outputs"].get("risk", {})
    personal_output = state["agent_outputs"].get("personalization", {})
    user_profile = state.get("user_profile", {})
    
    # 2. Build Council Prompt
    prompt = f"""
    You are the Senior Orchestrator of a multi-agent investment advisory system.
    Evaluate the analysis performed by your expert agents and make a final COUNCIL DECISION.

    --- AGENT FINDINGS ---
    1. SCOUT AGENT (Discovery):
       - Recommendations: {[r['ticker'] for r in scout_output.get('recommendations', [])]}
       - Reasoning Trace: {json.dumps(scout_output.get('reasoning_trace', []))}

    2. RISK GUARDIAN (Safety):
       - Verdict: {risk_output.get('verdict')}
       - Issue: {risk_output.get('issue')}
       - Est. Drawdown: {risk_output.get('metrics', {}).get('est_drawdown')}%

    3. PERSONALIZATION (Allocation):
       - Portfolio: {personal_output.get('portfolio')}

    --- USER CONSTRAINTS ---
    - Actual Risk Capacity: {user_profile.get('actual_risk_capacity')}/10
    - Max Drawdown: {user_profile.get('max_drawdown_pct')}%
    - Mismatch Warning: {user_profile.get('mismatch_warning')}

    --- DECISION CRITERIA ---
    1. Do agents agree or are there unresolved conflicts? (e.g., Risk says MODIFY but Scout didn't adjust).
    2. Does the final rupee allocation respect the user's surplus and risk appetite?
    3. Choose one:
       - APPROVE: The plan is solid and safe.
       - REJECT: Fundamental flaws that cannot be fixed by debate.
       - CONTINUE_DEBATE: Minor adjustments or more reasoning needed from Scout/Risk.

    Return ONLY a JSON object:
    {{
      "decision": "APPROVED" | "REJECTED" | "CONTINUE_DEBATE",
      "rationalization": "Detailed explanation of your choice",
      "debate_guidance": "If CONTINUE_DEBATE, what should agents reconsider?"
    }}
    """
    
    try:
        response = await llm.invoke([HumanMessage(content=prompt)])
        res_json = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        
        decision = res_json["decision"]
        rationalization = res_json["rationalization"]
    except Exception as e:
        logger.error(f"Error in Orchestrator Debate: {e}")
        # Default fallback
        decision = "APPROVED" if risk_output.get("verdict") == "APPROVE" else "REJECTED"
        rationalization = "Fallback triggered due to council error."
        res_json = {"debate_guidance": "None"}

    # 3. Update State
    state["decision"] = decision
    state["orchestrator_decision"] = {
        "decision": decision,
        "reasoning": rationalization,
        "iteration": state.get("iteration", 0),
        "guidance": res_json.get("debate_guidance")
    }
    
    state["agent_outputs"]["orchestrator"] = state["orchestrator_decision"]
    
    return state
