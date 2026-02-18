import logging
import json
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.llm_client import get_llm_client
from src.core.state import InvestmentState
from src.core.config import settings
from src.utils.orchestrator_utils import detect_strategy_conflicts, summarize_council_findings
# NEW: Import the safe fallback tool
from src.utils.scout_tools import find_safe_fallback_assets

logger = logging.getLogger("Orchestrator")

async def orchestrator_node(state: InvestmentState) -> InvestmentState:
    """
    The Orchestrator: Acts as the final judge (CIO).
    UPDATED: Implements Debate Logic and 'Safe Harbor' Fail-Safe.
    """
    current_round = state.get('iteration', 0)
    logger.info(f"--- NODE: Orchestrator Executive Review (Round {current_round}) ---")
    
    # Rate Limit Defense
    await asyncio.sleep(1)

    # 1. Gather Evidence
    auto_feedback = detect_strategy_conflicts(
        state["market_context"], 
        state["risk_assessment"], 
        state["user_profile"]
    )
    council_summary = summarize_council_findings(state)
    llm_client = get_llm_client()
    
    # 2. System Prompt asking for specific feedback
    system_prompt = f"""You are the CIO. Review the council findings.
    
    COUNCIL SUMMARY:
    {council_summary}
    
    AUTOMATED AUDIT:
    {json.dumps(auto_feedback) if auto_feedback else "No hard violations."}
    
    DECISION GUIDELINES:
    1. APPROVE: If the portfolio is safe and aligns with the market.
    2. CONTINUE_DEBATE: If risky, you MUST provide feedback to the Scout.
    
    OUTPUT FORMAT (JSON Only):
    {{
        "decision": "APPROVE" | "CONTINUE_DEBATE",
        "reasoning": "Explanation...",
        "feedback_for_scout": {{
            "violation_type": "Risk/Sector/Allocation",
            "reasoning": "Specific instruction on what to fix."
        }}
    }}
    """

    # Default to CONTINUE_DEBATE to encourage improvement unless fatal error
    decision_data = {
        "decision": "CONTINUE_DEBATE", 
        "reasoning": "Initial analysis pending."
    }

    try:
        response = await llm_client.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Provide your verdict.")
        ])
        
        # Smart JSON Parsing
        content = response.content
        s, e = content.find('{'), content.rfind('}')
        if s != -1 and e != -1:
            decision_data = json.loads(content[s:e+1])
            
        # --- THE FAIL-SAFE LOGIC ---
        # If we have argued for too many rounds, we STOP debating and Force-Approve ETFs.
        if current_round >= settings.max_debate_iterations:
            logger.warning(f"⚠️ Max debate rounds ({settings.max_debate_iterations}) reached.")
            
            if decision_data.get("decision") != "APPROVE":
                logger.info("🛡️ ACTIVATING FAIL-SAFE: Overwriting risky picks with Safe ETFs.")
                
                # 1. Force Approval
                decision_data["decision"] = "APPROVE"
                decision_data["reasoning"] = "Council deadlock resolved by deploying Safe Harbor ETFs."
                
                # 2. INJECT SAFE ASSETS directly into the State
                # This overwrites whatever risky stocks the Scout found
                safe_portfolio = find_safe_fallback_assets()
                state["scout_recommendations"] = safe_portfolio
        # ---------------------------

    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        # On crash, default to Safe Approval to ensure user gets a result
        decision_data["decision"] = "APPROVE"
        decision_data["reasoning"] = "System recovered from error using Safe Mode."
        state["scout_recommendations"] = find_safe_fallback_assets()

    # Update State
    state["decision"] = decision_data.get("decision", "APPROVE")
    state["orchestrator_decision"] = decision_data
    state["feedback_for_scout"] = decision_data.get("feedback_for_scout") or auto_feedback
    
    # Increment Global Iteration Counter
    state["iteration"] = current_round + 1
    
    logger.info(f"📢 ORCHESTRATOR VERDICT: {state['decision']}")
    return state