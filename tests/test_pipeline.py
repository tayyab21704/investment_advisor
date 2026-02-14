import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage
from src.agents.market_node import market_node
from src.agents.scout_node import scout_node
from src.agents.risk_node import risk_node
from src.core.state import InvestmentState

# --- HELPER TO PRINT THE PIPELINE ---
def print_pipeline_stage(stage_name, state_data):
    print(f"\n\n🚀 STAGE: {stage_name}")
    print("="*60)
    print(json.dumps(state_data, indent=2, default=str))
    print("="*60)

@pytest.mark.asyncio
async def test_full_investment_pipeline():
    """
    Simulates the full flow: Market -> Scout -> Risk.
    Scenario: User Risk 7/10 (Moderate Aggressive).
    """
    # 1. INITIAL STATE
    state: InvestmentState = {
        "user_id": "test_user",
        "user_profile": {"actual_risk_capacity": 7}, # Moderate-Aggressive
        "market_context": {},
        "scout_recommendations": [],
        "risk_assessment": {},
        "agent_outputs": {},
        "iteration": 0
    }

    # --- MOCKING THE TOOLS & LLM ---
    # We mock everything to ensure a deterministic test without real API calls.
    
    with patch("src.agents.market_node.get_llm_client") as mock_llm_m, \
         patch("src.agents.scout_node.get_llm_client") as mock_llm_s, \
         patch("src.agents.risk_node.get_llm_client") as mock_llm_r:

        # --- AGENT 1: MARKET AGENT ---
        # Mock LLM to skip tool calling and just give the final answer
        # (We assume the ReAct loop worked, as tested previously)
        mock_llm_m.return_value.bind_tools.return_value.invoke = AsyncMock(return_value=AIMessage(
            content='```json\n{"regime": "RISK_ON", "confidence": 0.9, "reasoning": "VIX < 15, Tech Rally"}\n```'
        ))
        
        print("\n\n🏁 STARTING PIPELINE TEST...")
        
        # EXECUTE MARKET NODE
        state = await market_node(state)
        print_pipeline_stage("MARKET AGENT", state["market_context"])
        
        assert state["market_context"]["regime"] == "RISK_ON"


        # --- AGENT 2: SCOUT AGENT ---
        # Mock Scout LLM to pick TCS and BTC based on "RISK_ON"
        mock_llm_s.return_value.bind_tools.return_value.invoke = AsyncMock(return_value=AIMessage(
            content='```json\n[{"ticker": "TCS.NS", "reasoning": "Tech Leader"}, {"ticker": "BTC-USD", "reasoning": "Crypto Alpha"}]\n```'
        ))
        
        # Patch Scout Tools (so it finds tickers)
        mock_scout_tools = {
            "get_universe_by_regime": lambda regime: ["TCS.NS", "BTC-USD"],
            "analyze_ticker": lambda ticker: {"ticker": ticker, "quality_score": 85},
            "get_vibe_check": lambda ticker: "Positive"
        }
        
        with patch.dict("src.agents.scout_node.tool_map", mock_scout_tools, clear=True):
            # EXECUTE SCOUT NODE
            state = await scout_node(state)
            
        print_pipeline_stage("SCOUT AGENT", state["scout_recommendations"])
        assert len(state["scout_recommendations"]) == 2


        # --- AGENT 3: RISK AGENT ---
        # Mock Risk Tools to return "High but Acceptable" risk
        mock_risk_tools = {
            "get_comprehensive_risk_metrics": lambda tickers: {
                "volatility": 18.5, # Moderate
                "beta": 1.1,        # Matches User Limit (1.1 for Risk 7)
                "var_95": -2.5,
                "max_drawdown": -15.0
            },
            "analyze_diversification": lambda tickers: {"avg_correlation": 0.4, "status": "Diversified"},
            "run_stress_test": lambda tickers: {"expected_loss": -20.0}
        }

        # Mock Risk LLM to APPROVE
        mock_llm_r.return_value.bind_tools.return_value.invoke = AsyncMock(return_value=AIMessage(
            content='```json\n{"verdict": "APPROVE", "metrics": {"beta": 1.1}, "reasoning": "Beta 1.1 matches moderate profile."}\n```'
        ))

        with patch.dict("src.agents.risk_node.tool_map", mock_risk_tools, clear=True):
            # EXECUTE RISK NODE
            state = await risk_node(state)

        print_pipeline_stage("RISK AGENT", state["risk_assessment"])
        
        # FINAL ASSERTIONS
        assert state["risk_assessment"]["verdict"] == "APPROVE"
        assert state["decision"] == "APPROVE"
        print("\n✅ PIPELINE TEST PASSED: Market -> Scout -> Risk -> Approved")