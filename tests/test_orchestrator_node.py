import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage
from src.agents.orchestrator_debate_node import orchestrator_node

# --- TEST 1: SUCCESSFUL APPROVAL ---
@pytest.mark.asyncio
async def test_orchestrator_approval():
    """
    Verifies that the Orchestrator approves when Risk and Market are aligned.
    """
    state = {
        "user_profile": {"max_beta": 1.2},
        "market_context": {"regime": "RISK_ON", "confidence": 0.9},
        "scout_recommendations": [{"ticker": "TCS.NS"}],
        "risk_assessment": {
            "verdict": "APPROVE", 
            "metrics": {"beta": 0.9}, 
            "reasoning": "Portfolio is safe."
        },
        "iteration": 0,
        "agent_outputs": {}
    }

    with patch("src.agents.orchestrator_debate_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke = AsyncMock()
        
        # Simulate AI Approval
        mock_llm.invoke.return_value = AIMessage(content=json.dumps({
            "decision": "APPROVED",
            "reasoning": "Council is in agreement and risk is within limits."
        }))
        mock_get_llm.return_value = mock_llm

        final_state = await orchestrator_node(state)
        
        assert final_state["decision"] == "APPROVED"
        assert final_state["orchestrator_decision"]["decision"] == "APPROVED"
        print("\n✅ Orchestrator Approval Test Passed!")

# --- TEST 2: AUTOMATED CONFLICT DETECTION (LOOP BACK) ---
@pytest.mark.asyncio
async def test_orchestrator_debate_loop():
    """
    Verifies that the Orchestrator detects a high beta and requests a debate.
    """
    # Setting Beta to 1.5 when limit is 1.2 triggers the code-based conflict detector
    state = {
        "user_profile": {"max_beta": 1.2},
        "market_context": {"regime": "RISK_OFF", "confidence": 0.8},
        "scout_recommendations": [{"ticker": "BTC-USD"}],
        "risk_assessment": {
            "verdict": "APPROVE", # Even if Risk Agent missed it, Orchestrator Utils should catch it
            "metrics": {"beta": 1.5}
        },
        "iteration": 0,
        "agent_outputs": {}
    }

    with patch("src.agents.orchestrator_debate_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke = AsyncMock()
        
        # AI sees the automated audit and decides to debate
        mock_llm.invoke.return_value = AIMessage(content=json.dumps({
            "decision": "CONTINUE_DEBATE",
            "reasoning": "Beta is too high for current regime.",
            "feedback_for_scout": {
                "violation_type": "High Beta",
                "offending_tickers": ["BTC-USD"],
                "suggested_action": "Replace with low-beta stocks."
            }
        }))
        mock_get_llm.return_value = mock_llm

        final_state = await orchestrator_node(state)
        
        assert final_state["decision"] == "CONTINUE_DEBATE"
        assert "BTC-USD" in final_state["feedback_for_scout"]["offending_tickers"]
        print("✅ Orchestrator Debate/Feedback Test Passed!")

# --- TEST 3: ITERATION SAFETY VALVE ---
@pytest.mark.asyncio
async def test_orchestrator_max_iterations():
    """
    Ensures the Orchestrator stops loops after reaching settings.max_debate_iterations.
    """
    from src.core.config import settings

    state = {
        "user_profile": {"max_beta": 1.2},
        "market_context": {"regime": "RISK_OFF"},
        "scout_recommendations": [],
        "risk_assessment": {"verdict": "REJECT", "metrics": {"beta": 2.0}},
        "iteration": settings.max_debate_iterations, # Force hit the limit
        "agent_outputs": {}
    }

    with patch("src.agents.orchestrator_debate_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke = AsyncMock()
        
        # AI wants to continue, but code should override to REJECTED
        mock_llm.invoke.return_value = AIMessage(content=json.dumps({
            "decision": "CONTINUE_DEBATE",
            "reasoning": "Still not right, try again."
        }))
        mock_get_llm.return_value = mock_llm

        final_state = await orchestrator_node(state)
        
        assert final_state["decision"] == "REJECTED" # Overridden by safety valve
        print("✅ Orchestrator Iteration Safety Valve Test Passed!")