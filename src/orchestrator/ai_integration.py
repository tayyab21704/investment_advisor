"""
AI Engine integration for orchestrator.

Handles loading AI engine from environment and provides utilities
for AI-powered evaluation of council debates.
"""

import logging
from typing import Optional, Any
from src.config.llm_config import AIEngineFactory

logger = logging.getLogger(__name__)


def load_ai_engine_from_env() -> Optional[Any]:
    """
    Load AI engine from environment configuration.
    
    Returns:
        AI engine instance or None if not configured/disabled
        
    Raises:
        ValueError: If API keys are missing for configured engine type
    """
    try:
        engine = AIEngineFactory.create_engine()
        
        if engine:
            logger.info(f"AI Engine loaded: {engine.engine_type}")
        else:
            logger.info("Running without AI Engine (AI_ENGINE_TYPE not set)")
        
        return engine
    
    except ValueError as e:
        logger.error(f"Failed to load AI Engine: {e}")
        logger.error("Set AI_ENGINE_TYPE to empty string to run without AI, or add API keys to .env")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading AI Engine: {e}")
        raise


def evaluate_with_ai(
    ai_engine: Any,
    agent_outputs: list[dict],
    user_profile: dict,
    asset_candidate: dict,
    iteration: int,
    max_iterations: int
) -> dict:
    """
    Use AI engine to evaluate council debate.
    
    Args:
        ai_engine: AI engine instance
        agent_outputs: List of AgentOutput dicts from all agents
        user_profile: User investment profile
        asset_candidate: Asset being evaluated
        iteration: Current iteration number
        max_iterations: Maximum allowed iterations
        
    Returns:
        Evaluation result with 'action' (REITERATE/TERMINATE), 'reason', 'reasoning'
    """
    
    if not ai_engine:
        logger.warning("evaluate_with_ai called but ai_engine is None")
        return {
            'action': 'REITERATE',
            'reason': 'NO_AI_ENGINE',
            'reasoning': 'AI engine not configured'
        }
    
    # Build analysis summary from agent outputs
    analysis_summary = "\n\n".join([
        f"[{o['agent_name'].upper()}]\nAnalysis: {o.get('analysis_log', 'No analysis provided')}\n"
        f"Verdict: {o['verdict']} | Confidence: {o['confidence']}"
        for o in agent_outputs
    ])
    
    # Highlight devil's advocate warnings
    devil_advocate = next(
        (o for o in agent_outputs if o['agent_name'] == 'devils_advocate'),
        None
    )
    devil_context = ""
    if devil_advocate:
        devil_context = f"\n\nDEVIL'S ADVOCATE SPECIFICALLY WARNS:\n{devil_advocate.get('analysis_log', 'N/A')}"
    
    # Build prompt for AI
    prompt = f"""
You are evaluating an investment council debate. Your job is to decide if the debate should:
- TERMINATE: Council has reached consensus, ready to proceed with investment
- REITERATE: More debate needed, contradictions to resolve, or insufficient confidence

INVESTMENT CONTEXT:
User Profile: {user_profile}
Asset Being Evaluated: {asset_candidate}
Current Iteration: {iteration} of {max_iterations}

AGENT ANALYSIS (Read all carefully - these are their detailed reasoning):
{analysis_summary}
{devil_context}

DECISION RULES:
1. If debate is genuinely stalled (contradictions not resolving) → TERMINATE and move on
2. If there are solvable concerns → REITERATE to address them
3. If agents have conflicts but low overall confidence → REITERATE for clarity
4. If devil's advocate raises critical risks → REITERATE to investigate further
5. If majority show strong agreement + devil's advocate is satisfied → TERMINATE

Based on the analysis above, should we REITERATE or TERMINATE?

Respond with ONLY valid JSON (no other text):
{{"action": "REITERATE" or "TERMINATE", "reason": "brief_reason", "reasoning": "detailed_explanation"}}
"""
    
    try:
        result = ai_engine.reason(prompt)
        logger.info(f"AI evaluation result: {result.get('action')} ({result.get('reason')})")
        return result
    
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        logger.error("Falling back to default REITERATE")
        return {
            'action': 'REITERATE',
            'reason': 'AI_ERROR',
            'reasoning': f"AI evaluation error: {str(e)}"
        }
