import asyncio
import logging
from src.orchestrator.graph import create_investment_graph
from src.core.config import setup_logging

async def run_council_debate_test():
    setup_logging()
    logger = logging.getLogger("CouncilTest")
    
    logger.info("Initializing 'Council Debate' Graph...")
    graph = create_investment_graph()
    
    # Simulate a user with a slight behavioral mismatch
    initial_state = {
        "user_id": "real_rebuild_user",
        "behavioral_answers": [3, 1, 3], # Mixed: Aggressive reaction, Conservative goal, Aggressive allocation
        "user_profile": {},
        "market_context": {},
        "scout_recommendations": [],
        "risk_assessment": {},
        "final_portfolio": [],
        "agent_outputs": {},
        "iteration": 0,
        "decision": "PENDING",
        "error": None
    }
    
    logger.info("Starting Council Debate invocation...")
    try:
        final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})
        
        logger.info(f"--- COUNCIL DEBATE RESULTS ---")
        logger.info(f"Final Decision: {final_state['decision']}")
        logger.info(f"Iterations (Debate Rounds): {final_state['iteration']}")
        
        orch = final_state.get("orchestrator_decision", {})
        logger.info(f"Orchestrator Rationalization: {orch.get('reasoning')}")
        
        scout = final_state["agent_outputs"].get("scout", {})
        logger.info(f"Scout ReAct Trace Steps: {len(scout.get('reasoning_trace', []))}")
        
        portfolio = final_state.get("final_portfolio", [])
        if portfolio:
            logger.info("Generated Portfolio:")
            for item in portfolio:
                logger.info(f"  - {item['ticker']}: ₹{item['monthly_amount']}")

    except Exception as e:
        logger.exception(f"Council Debate failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_council_debate_test())
