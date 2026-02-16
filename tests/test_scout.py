import pytest
from unittest.mock import patch, AsyncMock
from src.agents.scout_node import scout_node
from src.core.state import InvestmentState
from langchain_core.messages import AIMessage
import json

# --- MOCK DATA ---
MOCK_RISK_ON_UNIVERSE = ["TCS.NS", "INFY.NS", "BTC-USD"]
MOCK_RISK_OFF_UNIVERSE = ["HINDUNILVR.NS", "GC=F"]

@pytest.mark.asyncio
async def test_scout_risk_on_scenario():
    """
    Test if Scout picks growth assets when Market is Bullish and User is Aggressive.
    """
    # 1. Setup State
    state: InvestmentState = {
        "user_profile": {"actual_risk_capacity": 8, "actual_risk_capacity": 8}, # 8/10 Risk
        "market_context": {"regime": "RISK_ON"},
        "iteration": 0,
        "scout_recommendations": [],
        "agent_outputs": {}
    }

    # 2. Mock Dependencies
    with patch("src.agents.scout_node.get_universe_by_regime") as mock_universe, \
         patch("src.agents.scout_node.analyze_ticker") as mock_analyze, \
         patch("src.agents.scout_node.get_vibe_check") as mock_vibe, \
         patch("src.agents.scout_node.get_llm_client") as mock_llm_getter:
        
        # Mock Tools
        mock_universe.return_value = MOCK_RISK_ON_UNIVERSE
        
        # Mock Analysis (High Quality Scores)
        mock_analyze.side_effect = lambda ticker: {
            "ticker": ticker, 
            "quality_score": 85, 
            "type": "crypto" if "USD" in ticker else "equity"
        }
        mock_vibe.return_value = "Positive news flow."

        # Mock LLM Final Decision (The JSON output)
        mock_llm = AsyncMock()
        mock_llm.invoke.return_value = AIMessage(content="""
            ```json
            [
                {"ticker": "TCS.NS", "name": "TCS", "reasoning": "Growth"},
                {"ticker": "BTC-USD", "name": "Bitcoin", "reasoning": "High Alpha"}
            ]
            ```
        """)
        mock_llm_getter.return_value = mock_llm

        # 3. Run Node
        final_state = await scout_node(state)

        # 4. Verify
        recommendations = final_state["scout_recommendations"]
        tickers = [r["ticker"] for r in recommendations]
        
        print(f"\n🔍 Risk-On Picks: {tickers}")
        assert "BTC-USD" in tickers
        assert final_state["agent_outputs"]["scout"]["iteration"] == 0
        assert len(final_state["agent_outputs"]["scout"]["reasoning_trace"]) > 0

@pytest.mark.asyncio
async def test_scout_revision_logic():
    """
    Test if Scout recognizes a revision loop (Iteration > 0) and adapts.
    """
    # 1. Setup State (Iteration = 1 implies a redo)
    state: InvestmentState = {
        "user_profile": {"actual_risk_capacity": 5},
        "market_context": {"regime": "NEUTRAL"},
        "iteration": 1, # <--- THIS IS KEY
        "risk_assessment": {"issue": "Too much crypto exposure"},
        "scout_recommendations": [],
        "agent_outputs": {}
    }

    with patch("src.agents.scout_node.get_universe_by_regime") as mock_universe, \
         patch("src.agents.scout_node.analyze_ticker") as mock_analyze, \
         patch("src.agents.scout_node.get_vibe_check") as mock_vibe, \
         patch("src.agents.scout_node.get_llm_client") as mock_llm_getter:
        
        mock_universe.return_value = ["HDFCBANK.NS", "SBIN.NS"]
        mock_analyze.return_value = {"ticker": "HDFCBANK.NS", "quality_score": 90}
        mock_vibe.return_value = "Stable."

        # Mock LLM acknowledging the revision
        mock_llm = AsyncMock()
        mock_llm.invoke.return_value = AIMessage(content="""
            [{"ticker": "HDFCBANK.NS", "reasoning": "Removed crypto as requested."}]
        """)
        mock_llm_getter.return_value = mock_llm

        # 3. Run Node
        final_state = await scout_node(state)

        # 4. Verify Trace
        trace = final_state["agent_outputs"]["scout"]["reasoning_trace"]
        first_thought = trace[0]["content"]
        
        print(f"\n🧠 Revision Thought: {first_thought}")
        assert "Revision requested" in first_thought or "Feedback" in first_thought