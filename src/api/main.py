from fastapi import FastAPI, HTTPException
from src.api.models import RecommendationRequest, RecommendationResponse
from src.orchestrator.graph import create_investment_graph
import logging
import uuid

# Setup Logging
from src.core.config import setup_logging
setup_logging()

logger = logging.getLogger("InvestmentAPI")

app = FastAPI(title="Investment AI: Council Debate Edition")
graph = create_investment_graph()

@app.get("/")
async def health(): 
    return {"status": "healthy", "edition": "Council Debate"}

@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Initializes the investment state and runs the Council Debate graph.
    """
    # 1. Initialize State
    initial_state = {
        "user_id": request.user_id,
        "behavioral_answers": request.behavioral_answers,
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
    
    try:
        # 2. Invoke Graph
        logger.info(f"Starting recommendation for user: {request.user_id}")
        final_state = await graph.ainvoke(initial_state)
        
        # 3. Format Response
        orch_decision = final_state.get("orchestrator_decision", {})
        
        return {
            "recommendation_id": f"rec_{uuid.uuid4().hex[:8]}",
            "status": final_state.get("decision", "ERROR"),
            "iteration_count": final_state.get("iteration", 0),
            "portfolio": final_state.get("final_portfolio", []),
            "orchestrator_rationalization": orch_decision.get("reasoning", "No rationalization available."),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "user_profile_summary": final_state.get("user_profile", {})
        }
        
    except Exception as e:
        logger.exception("Error during graph execution")
        raise HTTPException(status_code=500, detail=str(e))
