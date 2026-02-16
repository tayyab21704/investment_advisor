import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from src.agents.profiling_node import profiling_node
from src.core.state import InvestmentState

# --- HELPER TO PRINT REACT STEPS ---
def print_react_trace(agent_name, output_messages):
    print(f"\n\n🤖 {agent_name} REASONING TRACE:")
    print("="*60)
    
    for i, step in enumerate(output_messages):
        if isinstance(step, (SystemMessage, HumanMessage)):
            continue

        # 1. DETECT TOOL CALLS (The "Action")
        if hasattr(step, 'tool_calls') and step.tool_calls:
            for tool in step.tool_calls:
                print(f"🔨 ACTION: Calling Tool '{tool['name']}'")
                print(f"   └─ Args: {tool['args']}")
        
        # 2. DETECT TOOL OUTPUTS (The "Observation")
        elif isinstance(step, ToolMessage):
            print(f"👀 OBSERVATION: {step.content}")

        # 3. DETECT AI THOUGHTS (The "Reasoning")
        elif hasattr(step, 'content') and step.content:
            print(f"🧠 THOUGHT: {step.content}")
            
    print("="*60 + "\n")

@pytest.mark.asyncio
async def test_profiling_logic_standalone():
    """
    Tests the Profiling Agent using direct input.
    Simulates a user who is high-income but has a 'Panic' behavioral history.
    """
    
    # 1. MOCK INPUT DATA (Directly in State)
    raw_user_data = {
        "user_id": "test_standalone",
        "age": 28,
        "annual_income": 2000000, 
        "debt_amount": 100000,
        "job_type": "Private Sector",
        "emergency_fund_months": 2, # Low liquidity
        "demographic_risk_base": 8, # Young & High Income
        "questionnaire": {
            "q2_market_crash": "Sell everything", # Panic Flag
            "q9_volatility": "I get anxious"      # Anxiety Flag
        }
    }

    state: InvestmentState = {
        "raw_user_data": raw_user_data,
        "user_profile": {},
        "agent_outputs": {}
    }

    # 2. MOCK THE LLM CLIENT
    with patch("src.agents.profiling_node.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        # We mock 'gemini' because profiling_node uses 'llm.gemini' for create_react_agent
        mock_gemini = MagicMock()
        mock_gemini.ainvoke = AsyncMock()
        mock_llm.gemini = mock_gemini
        mock_get_llm.return_value = mock_llm

        # --- SIMULATE THE REACT CONVERSATION ---
        
        # Turn 1: Analyze Behavior
        r1 = AIMessage(content="I'll start by checking behavioral flags.", tool_calls=[{
            "name": "analyze_loss_aversion", 
            "args": {"questionnaire_responses": raw_user_data["questionnaire"]},
            "id": "c1"
        }])
        
        # Turn 2: Analyze Stability
        r2 = AIMessage(content="Behavior shows panic. Now checking stability.", tool_calls=[{
            "name": "analyze_income_stability",
            "args": {
                "annual_income": 2000000, 
                "debt_amount": 100000, 
                "job_type": "Private Sector", 
                "emergency_fund_months": 2
            },
            "id": "c2"
        }])

        # Turn 3: Calculate Final Score
        r3 = AIMessage(content="Stability is medium. Calculating final score.", tool_calls=[{
            "name": "calculate_final_risk_score",
            "args": {"demographic_risk_base": 8, "behavioral_penalty": 3, "stability_score": 8},
            "id": "c3"
        }])

        # Turn 4: Final JSON Response
        r4 = AIMessage(content='''
        ```json
        {
            "actual_risk_capacity": 5, 
            "risk_appetite": "Moderate", 
            "flags": ["panic_seller", "low_liquidity"]
        }
        ```
        ''')

        # Connect the sequence
        # create_react_agent calls ainvoke for each step
        mock_gemini.ainvoke.side_effect = [r1, r2, r3, r4]

        # 3. RUN THE NODE
        final_state = await profiling_node(state)

        # 4. VERIFY RESULTS
        profile = final_state["user_profile"]
        
        # Check if the node extracted the dictionary correctly
        assert isinstance(profile, dict)
        assert profile["actual_risk_capacity"] == 5
        
        # 5. PRINT THE TRACE
        # We simulate the message history for the printer
        # (In the actual node, this is handled inside create_react_agent)
        mock_history = [
            r1, 
            ToolMessage(content="{'behavioral_flags': ['panic_seller'], 'risk_penalty': 3}", tool_call_id="c1"),
            r2,
            ToolMessage(content="{'stability_score': 8, 'status': 'STABLE'}", tool_call_id="c2"),
            r3,
            ToolMessage(content="5", tool_call_id="c3"),
            r4
        ]
        print_react_trace("PROFILING AGENT", mock_history)

    print(f"✅ Standalone Profiling Test Passed. Result: {profile}")