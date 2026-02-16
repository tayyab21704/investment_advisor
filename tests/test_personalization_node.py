import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from src.agents.personalization_node import personalization_node

# --- HELPER: PRINT THE TRACE ---
def print_react_trace(agent_name, output_messages):
    print(f"\n\n🤖 {agent_name} REASONING TRACE:")
    print("="*60)
    for step in output_messages:
        if isinstance(step, (SystemMessage, HumanMessage)): continue
        
        # Detect Tool Calls (Actions)
        if hasattr(step, 'tool_calls') and step.tool_calls:
            for tool in step.tool_calls:
                print(f"🔨 ACTION: Calling Tool '{tool['name']}'")
                print(f"   └─ Args: {tool['args']}")
        
        # Detect Tool Outputs (Observations)
        elif isinstance(step, ToolMessage):
            print(f"👀 OBSERVATION: {step.content}")

        # Detect AI Reasoning (Thoughts)
        elif hasattr(step, 'content') and step.content:
            print(f"🧠 THOUGHT: {step.content}")
    print("="*60 + "\n")

# --- TEST 1: AGENTIC REASONING LOOP ---
@pytest.mark.asyncio
async def test_personalization_agent_react_loop():
    """
    Verifies the Personalization Agent uses tools to calculate and validate allocations.
    """
    state = {
        "user_profile": {
            "actual_risk_capacity": 6,
            "monthly_surplus": 20000,
            "liquidity_required_pct": 20,
            "max_single_asset_pct": 15
        },
        "scout_recommendations": [
            {"ticker": "TCS.NS", "name": "Tata Consultancy Services", "type": "equity"},
            {"ticker": "BTC-USD", "name": "Bitcoin", "type": "crypto"}
        ],
        "agent_outputs": {},
        "final_portfolio": []
    }

    with patch("src.agents.personalization_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_gemini = MagicMock()
        mock_gemini.ainvoke = AsyncMock()
        
        # 1. AI decides to calculate budget
        r1 = AIMessage(content="Calculating investable budget.", tool_calls=[{
            "name": "calculate_investable_amount",
            "args": {"monthly_surplus": 20000, "liquidity_required_pct": 20},
            "id": "c1"
        }])
        
        # 2. AI decides on a strategy and validates
        r2 = AIMessage(content="Budget is 16k. Validating equal allocation.", tool_calls=[{
            "name": "validate_allocation",
            "args": {
                "allocations": [
                    {"ticker": "TCS.NS", "monthly_investment": 8000, "allocation_pct": 50},
                    {"ticker": "BTC-USD", "monthly_investment": 8000, "allocation_pct": 50}
                ],
                "investable_amount": 16000,
                "max_single_asset_pct": 15
            },
            "id": "c2"
        }])
        
        # 3. Final Response (Agent realizes 50% exceeds the 15% limit, so it caps them)
        final_portfolio_json = [
            {"ticker": "TCS.NS", "monthly_investment": 2400, "allocation_pct": 15, "reasoning": "Capped at 15%"},
            {"ticker": "BTC-USD", "monthly_investment": 2400, "allocation_pct": 15, "reasoning": "Capped at 15%"}
        ]
        r3 = AIMessage(content=f"Validation failed for 50%. Capping at limits: {json.dumps(final_portfolio_json)}")

        mock_gemini.ainvoke.side_effect = [r1, r2, r3]
        mock_llm.gemini = mock_gemini
        mock_get_llm.return_value = mock_llm

        # Run the node
        final_state = await personalization_node(state)
        
        # Print the trace for visualization
        mock_history = [
            r1, 
            ToolMessage(content="{'investable_amount': 16000}", tool_call_id="c1"),
            r2,
            ToolMessage(content="{'valid': False, 'violations': ['Exceeds 15%']}", tool_call_id="c2"),
            r3
        ]
        print_react_trace("PERSONALIZATION AGENT", mock_history)

        assert len(final_state["final_portfolio"]) == 2
        assert final_state["final_portfolio"][0]["allocation_pct"] == 15
        print("✅ ReAct Reasoning Test Passed!")

# --- TEST 2: EMPTY RECOMMENDATIONS ---
@pytest.mark.asyncio
async def test_personalization_no_recs():
    """
    Verifies that the agent handles cases where Scout provides 0 assets.
    """
    state = {
        "user_profile": {"monthly_surplus": 10000},
        "scout_recommendations": [],
        "agent_outputs": {},
        "final_portfolio": []
    }
    
    final_state = await personalization_node(state)
    assert final_state["final_portfolio"] == []
    assert "error" in final_state["agent_outputs"]["personalization"]
    print("✅ Empty Recommendations Handling Passed!")