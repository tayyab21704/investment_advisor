"""
Evaluation and termination logic for the orchestrator.

Supports both deterministic rules-based evaluation and AI-based evaluation.
The orchestrator can switch between modes based on AI engine availability.
"""

import logging
from typing import Optional, Any
from src.orchestrator.state import CouncilState, EvaluationResult, AgentOutput

logger = logging.getLogger(__name__)


def evaluate_council(state: CouncilState) -> EvaluationResult:
    """
    Deterministic evaluation of all agent outputs.
    
    Decision tree:
    1. If ANY agent says REJECT → REITERATE
    2. If ANY agent has blocking_issues → REITERATE
    3. If average confidence < 0.75 → REITERATE
    4. Otherwise → TERMINATE with CONSENSUS
    
    Args:
        state: Current council state with all agent outputs
        
    Returns:
        EvaluationResult with action and reason
    """
    
    # Collect all agent outputs (filter out None values)
    outputs: list[AgentOutput] = [
        state.get("risk_qualification"),
        state.get("devils_advocate"),
        state.get("personal_suitability"),
        state.get("market_analysis"),
        state.get("feasibility_analysis"),
    ]
    outputs = [o for o in outputs if o is not None]
    
    if not outputs:
        # No agents have reported yet
        return EvaluationResult(
            action="REITERATE",
            reason="NO_OUTPUTS",
            details={"message": "Waiting for agent outputs"}
        )
    
    # Rule 1: Any REJECT is a blocker
    if any(o["verdict"] == "REJECT" for o in outputs):
        rejecting_agents = [o["agent_name"] for o in outputs if o["verdict"] == "REJECT"]
        return EvaluationResult(
            action="REITERATE",
            reason="REJECT",
            details={"rejecting_agents": rejecting_agents}
        )
    
    # Rule 2: Any blocking issues trigger reiteration
    blocking_agents = {
        o["agent_name"]: o["blocking_issues"]
        for o in outputs
        if o["blocking_issues"]
    }
    if blocking_agents:
        return EvaluationResult(
            action="REITERATE",
            reason="BLOCKING_ISSUES",
            details={"blocking_agents": blocking_agents}
        )
    
    # Rule 3: Low average confidence triggers reiteration
    avg_confidence = sum(o["confidence"] for o in outputs) / len(outputs)
    if avg_confidence < 0.75:
        return EvaluationResult(
            action="REITERATE",
            reason="LOW_CONFIDENCE",
            details={
                "average_confidence": avg_confidence,
                "threshold": 0.75,
                "agent_confidences": {o["agent_name"]: o["confidence"] for o in outputs}
            }
        )
    
    # Rule 4: Consensus reached
    return EvaluationResult(
        action="TERMINATE",
        reason="CONSENSUS",
        details={
            "average_confidence": avg_confidence,
            "verdicts": {o["agent_name"]: o["verdict"] for o in outputs},
            "agent_count": len(outputs)
        }
    )


def should_terminate(state: CouncilState) -> bool:
    """
    Check if orchestrator should terminate.
    
    Considers:
    - Evaluation result
    - Max iteration limit
    - Explicit termination flag
    """
    evaluation = evaluate_council(state)
    max_iterations = state.get("max_iterations", 5)
    current_iteration = state.get("iteration", 0)
    
    # Hard limit on iterations
    if current_iteration >= max_iterations:
        return True
    
    # Orchestrator says terminate
    if evaluation["action"] == "TERMINATE":
        return True
    
    return False


def evaluate_with_ai_engine(
    ai_engine: Optional[Any],
    state: CouncilState,
    user_profile: dict,
    asset_candidate: dict
) -> EvaluationResult:
    """
    Use AI engine to intelligently evaluate council debate.
    
    The AI engine reads all agent reasoning/logic boxes and makes decisions
    based on nuanced analysis, not just hard rules.
    
    Args:
        ai_engine: AI engine instance (Gemini, OpenAI, or None)
        state: Current council state with all agent outputs
        user_profile: User investment profile
        asset_candidate: Asset being evaluated
        
    Returns:
        EvaluationResult with action and AI reasoning
    """
    
    # Collect all agent outputs (filter out None values)
    outputs: list[AgentOutput] = [
        state.get("risk_qualification"),
        state.get("devils_advocate"),
        state.get("personal_suitability"),
        state.get("market_analysis"),
        state.get("feasibility_analysis"),
    ]
    outputs = [o for o in outputs if o is not None]
    
    if not outputs:
        # No agents have reported yet
        return EvaluationResult(
            action="REITERATE",
            reason="NO_OUTPUTS",
            details={"message": "Waiting for agent outputs"}
        )
    
    # If no AI engine, fall back to deterministic rules
    if not ai_engine:
        logger.info("No AI engine available, using deterministic evaluation")
        return evaluate_council(state)
    
    # Build detailed analysis from agent reasoning
    agent_analysis = []
    for output in outputs:
        agent_analysis.append({
            "agent": output["agent_name"],
            "verdict": output["verdict"],
            "confidence": output["confidence"],
            "key_findings": output["key_findings"],
            "blocking_issues": output["blocking_issues"],
            "recommendations": output["recommendations"],
            "reasoning": output.get("reasoning", "No reasoning provided"),
            "metrics": output.get("metrics", {})
        })
    
    # Build prompt for AI with full reasoning
    analysis_text = "\n\n".join([
        f"""
AGENT: {a['agent']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict: {a['verdict']} | Confidence: {a['confidence']*100:.0f}%

REASONING/LOGIC BOX:
{a['reasoning']}

Key Findings: {', '.join(a['key_findings'])}
Blocking Issues: {a['blocking_issues'] if a['blocking_issues'] else 'None'}
Recommendations: {', '.join(a['recommendations'])}
"""
        for a in agent_analysis
    ])
    
    prompt = f"""
You are an investment council chairman. Review this debate and decide whether to:
- REITERATE: Continue debate, more analysis needed
- TERMINATE: Sufficient consensus, proceed with investment

INVESTMENT CONTEXT:
User Risk Tolerance: {user_profile.get('risk_tolerance', 'Unknown')}
Investment Horizon: {user_profile.get('investment_horizon_months', 0)} months
Asset Type: {asset_candidate.get('asset_type', 'Unknown')}
Sector: {asset_candidate.get('sector', 'Unknown')}

COUNCIL ANALYSIS (Read the reasoning carefully):
{analysis_text}

DECISION CRITERIA:
1. If all agents agree → TERMINATE
2. If most agents agree and devil's advocate satisfied → TERMINATE
3. If key concerns unresolved → REITERATE
4. If low confidence overall → REITERATE
5. If blocking issues present → REITERATE
6. If contradictions need resolution → REITERATE

Based on the analysis and reasoning above, respond with ONLY valid JSON:
{{"action": "REITERATE" or "TERMINATE", "reason": "key_reason", "ai_reasoning": "detailed_explanation_of_why"}}
"""
    
    try:
        result = ai_engine.reason(prompt)
        
        # Parse AI response
        action = result.get("action", "REITERATE").upper()
        if action not in ["REITERATE", "TERMINATE"]:
            action = "REITERATE"
        
        logger.info(f"AI Evaluation: {action} - {result.get('reason', 'No reason')}")
        
        return EvaluationResult(
            action=action,
            reason=f"AI_DECISION: {result.get('reason', 'No reason')}",
            details={
                "ai_reasoning": result.get("ai_reasoning", "No reasoning"),
                "agent_verdicts": {a["agent"]: a["verdict"] for a in agent_analysis},
                "agent_confidences": {a["agent"]: a["confidence"] for a in agent_analysis},
                "total_agents": len(outputs)
            }
        )
    
    except Exception as e:
        logger.error(f"AI evaluation error: {e}, falling back to rules-based")
        # Fall back to deterministic evaluation
        return evaluate_council(state)
