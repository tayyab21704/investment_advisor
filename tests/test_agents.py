import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from src.agents.market_node import market_node
from src.agents.scout_node import scout_node

# --- HELPER TO PRINT REACT STEPS ---
def print_react_trace(agent_name, output):
    print(f"\n\n🤖 {agent_name} REASONING TRACE:")
    print("="*60)
    
    # Handle different keys for market vs scout
    steps = output.get("messages", []) if "messages" in output else output.get("trace", [])
    
    for i, step in enumerate(steps):
        # Skip System Messages for cleaner logs
        if isinstance(step, SystemMessage):
            continue

        # 1. DETECT TOOL CALLS (The "Action")
        if hasattr(step, 'tool_calls') and step.tool_calls:
            for tool in step.tool_calls:
                print(f"🔨 ACTION: Calling Tool '{tool['name']}'")
                print(f"   └─ Args: {tool['args']}")
        
        # 2. DETECT TOOL OUTPUTS (The "Observation")
        elif isinstance(step, ToolMessage):
            # Truncate long JSON for readability
            content = str(step.content)
            if len(content) > 120: content = content[:120] + "..."
            print(f"👀 OBSERVATION: {content}")

        # 3. DETECT AI THOUGHTS (The "Reasoning")
        elif hasattr(step, 'content') and step.content:
            print(f"🧠 THOUGHT: {step.content}")
            
    print("="*60 + "\n")


@pytest.mark.asyncio
async def test_market_agent_react_loop():
    """
    Visualizes the Market Agent's thought process.
    """
    state = {
        "user_id": "test", 
        "market_context": {}, 
        "agent_outputs": {}, 
        "user_profile": {"actual_risk_capacity": 5}
    }

    # Mock the LLM Client
    with patch("src.agents.market_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_bound = MagicMock()
        mock_bound.invoke = AsyncMock()
        
        # Define the Agent's conversation flow
        # Step 1: "I need to check VIX" (Thought + Tool Call)
        r1 = AIMessage(
            content="I need to check VIX.", 
            tool_calls=[{"name": "fetch_market_indicators", "args": {}, "id": "1"}]
        )
        # Step 2: "VIX is low. Checking breadth." (Thought + Tool Call)
        r2 = AIMessage(
            content="VIX is low. Checking breadth.", 
            tool_calls=[{"name": "fetch_sectoral_breadth", "args": {}, "id": "2"}]
        )
        # Step 3: Final Answer
        r3 = AIMessage(
            content='```json\n{"regime": "RISK_ON", "confidence": 0.9, "reasoning": "VIX is low."}\n```'
        )
        
        mock_bound.invoke.side_effect = [r1, r2, r3]
        mock_llm.bind_tools.return_value = mock_bound
        mock_get_llm.return_value = mock_llm

        # Patch the tool_map directly to use mocks
        mock_tools = {
            "fetch_market_indicators": lambda: {"vix": 12, "trend": "BULLISH"},
            "fetch_sectoral_breadth": lambda: {"IT": "BULLISH", "BANK": "BULLISH"}
        }

        with patch.dict("src.agents.market_node.tool_map", mock_tools, clear=True):
            final_state = await market_node(state)
            print_react_trace("MARKET AGENT", final_state["agent_outputs"]["market"])


@pytest.mark.asyncio
async def test_scout_agent_react_loop():
    """
    Visualizes the Scout Agent's thought process.
    """
    state = {
        "user_profile": {"actual_risk_capacity": 8},
        "market_context": {"regime": "RISK_ON"},
        "scout_recommendations": [],
        "agent_outputs": {},
        "iteration": 0
    }

    with patch("src.agents.scout_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_bound = MagicMock()
        mock_bound.invoke = AsyncMock()

        # Conversation Flow
        r1 = AIMessage(content="Getting universe.", tool_calls=[{"name": "get_universe_by_regime", "args": {"regime": "RISK_ON"}, "id": "1"}])
        r2 = AIMessage(content="Checking TCS.", tool_calls=[{"name": "analyze_ticker", "args": {"ticker": "TCS"}, "id": "2"}])
        r3 = AIMessage(content='```json\n[{"ticker": "TCS", "reasoning": "Growth"}]\n```')
        
        mock_bound.invoke.side_effect = [r1, r2, r3]
        mock_llm.bind_tools.return_value = mock_bound
        mock_get_llm.return_value = mock_llm

        # Patch Scout tools
        mock_scout_tools = {
            "get_universe_by_regime": lambda regime: ["TCS"],
            "analyze_ticker": lambda ticker: {"ticker": "TCS", "quality_score": 90},
            "get_vibe_check": lambda ticker: "Good"
        }

        with patch.dict("src.agents.scout_node.tool_map", mock_scout_tools, clear=True):
            final_state = await scout_node(state)
            print_react_trace("SCOUT AGENT", final_state["agent_outputs"]["scout"])