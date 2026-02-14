from langgraph.graph import StateGraph, END
from src.core.state import InvestmentState
import logging

# Import Nodes
from src.agents.profiling_node import profiling_node
from src.agents.market_node import market_node
from src.agents.scout_node import scout_node
from src.agents.risk_node import risk_node
from src.agents.personalization_node import personalization_node
from src.agents.orchestrator_debate_node import orchestrator_debate_node

logger = logging.getLogger("InvestmentGraph")

def create_investment_graph():
    """
    Creates the 'Council Debate' LangGraph workflow.
    """
    workflow = StateGraph(InvestmentState)

    # 1. Add all nodes
    workflow.add_node("profiling", profiling_node)
    workflow.add_node("market", market_node)
    workflow.add_node("scout", scout_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("personalization", personalization_node)
    workflow.add_node("orchestrator", orchestrator_debate_node)

    # 2. Set Entry Point
    workflow.set_entry_point("profiling")

    # 3. Linear basic flow
    workflow.add_edge("profiling", "market")
    workflow.add_edge("market", "scout")
    workflow.add_edge("scout", "risk")

    # 4. Conditional Edge: Risk -> Scout (MODIFY loop)
    def route_after_risk(state: InvestmentState):
        verdict = state["risk_assessment"].get("verdict")
        if verdict == "MODIFY":
            logger.info("--- ROUTE: Risk Guardian requested MODIFY. Looping back to Scout. ---")
            return "scout"
        return "personalization"

    workflow.add_conditional_edges(
        "risk",
        route_after_risk,
        {
            "scout": "scout",
            "personalization": "personalization"
        }
    )

    # 5. Connect Personalization to Orchestrator Debate
    workflow.add_edge("personalization", "orchestrator")

    # 6. Conditional Edge: Orchestrator -> Scout (CONTINUE_DEBATE loop)
    def route_after_orchestrator(state: InvestmentState):
        decision = state["orchestrator_decision"].get("decision")
        iteration = state.get("iteration", 0)
        
        if decision == "CONTINUE_DEBATE" and iteration < 3: # Cap at 3 debate rounds
            logger.info(f"--- ROUTE: Council requested CONTINUE_DEBATE (Round {iteration+1}). Looping to Scout. ---")
            state["iteration"] = iteration + 1
            return "scout"
        
        logger.info(f"--- ROUTE: Final Decision: {decision}. Workflow terminating. ---")
        return END

    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "scout": "scout",
            END: END
        }
    )

    # 7. Compile
    return workflow.compile()
