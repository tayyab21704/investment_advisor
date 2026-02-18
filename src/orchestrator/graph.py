import logging
from langgraph.graph import StateGraph, END

# Import the shared state
from src.core.state import InvestmentState

# Import all your agent nodes
from src.agents.market_node import market_node
from src.agents.scout_node import scout_node
from src.agents.risk_node import risk_node
from src.agents.orchestrator_debate_node import orchestrator_node
from src.agents.personalization_node import personalization_node

from langgraph.checkpoint.memory import MemorySaver


memory = MemorySaver()


logger = logging.getLogger("InvestmentGraph")

def orchestrator_routing(state: InvestmentState) -> str:
    """
    The Decision Junction: Determines where the state goes after the Orchestrator.
    """
    decision = state.get("decision", "REJECTED")
    
    if decision == "APPROVE":
        logger.info("✅ Orchestrator APPROVED. Moving to Personalization.")
        return "personalize"
    
    elif decision == "CONTINUE_DEBATE":
        logger.info(f"🔄 Orchestrator requested DEBATE (Round {state.get('iteration')}). Looping back to Scout.")
        return "scout"
    
    else:
        logger.warning("❌ Orchestrator REJECTED. Ending workflow.")
        return "__end__"

def create_investment_council():
    """
    Assembles the multi-agent council into a stateful graph.
    """
    # Initialize the graph with your custom State
    workflow = StateGraph(InvestmentState)

    # 1. Register all Nodes
    workflow.add_node("market_analysis", market_node)
    workflow.add_node("scout", scout_node)
    workflow.add_node("risk_audit", risk_node) # Corrected name
    workflow.add_node("orchestrate", orchestrator_node)
    workflow.add_node("personalize", personalization_node)

    # 2. Define the Linear Path
    workflow.set_entry_point("market_analysis")
    
    # Sequence: Market -> Scout -> Risk -> Orchestrate
    workflow.add_edge("market_analysis", "scout")
    workflow.add_edge("scout", "risk_audit") # This was missing!
    workflow.add_edge("risk_audit", "orchestrate")

    # 3. Define the Self-Correction Loop (Conditional Edges)
    workflow.add_conditional_edges(
        "orchestrate",
        orchestrator_routing,
        {
            "personalize": "personalize", # Approval Path
            "scout": "scout",             # Revision Path (The Loop)
            "__end__": END                # Rejection Path
        }
    )

    # 4. The Final Step
    workflow.add_edge("personalize", END)

    # Compile the graph into an executable runnable
    return workflow.compile(checkpointer=memory) # Enables state persistence

# Global instance for the application
council_app = create_investment_council()