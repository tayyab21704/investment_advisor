# Risk Qualification Agent - Connection Guide

## What This Agent Does

Analyzes if an investment fits the user's risk tolerance.

## Input Received

```python
{
    "user_profile": UserProfile,        # User risk tolerance, horizon
    "asset_candidate": AssetCandidate,  # Asset type, sector, return
    "market_context": MarketContext,    # Market trend, volatility
    "position": Position                # Investment amount, % of portfolio
}
```

## What To Return

Must return `AgentOutput`:

```python
from src.orchestrator.state import AgentOutput

AgentOutput(
    agent_name="risk_qualification",
    verdict="APPROVE",              # or MODIFY, REJECT
    confidence=0.85,                # 0.0 to 1.0
    key_findings=[
        "Risk score: 45/100",
        "User tolerance: 50/100",
        "Within safe range"
    ],
    blocking_issues=[],             # Empty if no blockers
    recommendations=[
        "Monitor weekly",
        "Set stop-loss at 8%"
    ],
    reasoning="""Risk Analysis:
    1. Analyzed user profile
    2. Calculated asset risk
    3. Compared with tolerance
    4. Decision: APPROVED""",
    metrics={
        "risk_score": 45,
        "user_threshold": 50,
        "variance": 5
    }
)
```

## How To Connect

### Step 1: Build Your Agent Function

```python
# src/agents/risk_agent.py
from src.orchestrator.state import AgentOutput

def analyze_risk(agent_input: dict) -> AgentOutput:
    user = agent_input.get("user_profile", {})
    asset = agent_input.get("asset_candidate", {})
    market = agent_input.get("market_context", {})
    position = agent_input.get("position", {})

    # YOUR LOGIC HERE
    risk_score = calculate_risk(asset, market)
    user_risk = get_user_risk_threshold(user)

    verdict = "APPROVE" if risk_score < user_risk else "REJECT"

    return AgentOutput(
        agent_name="risk_qualification",
        verdict=verdict,
        confidence=0.85,
        key_findings=["Score: X", "Threshold: Y"],
        blocking_issues=[],
        recommendations=["Monitor risk"],
        reasoning="Your detailed analysis here",
        metrics={"risk_score": risk_score, "threshold": user_risk}
    )
```

### Step 2: Register with Orchestrator

```python
from src.orchestrator import Orchestrator
from src.agents.risk_agent import analyze_risk

orchestrator = Orchestrator()
orchestrator.register_agent("risk_qualification", analyze_risk)
```

### Step 3: Done

When orchestrator runs, it will:

1. Collect your inputs automatically
2. Call your function
3. Expect AgentOutput back
4. Read your reasoning for AI decision

## Key Requirements

✓ Function name can be anything  
✓ Must accept `dict` input  
✓ Must return exactly `AgentOutput` format  
✓ Must include `reasoning` field  
✓ `agent_name` MUST be "risk_qualification"  
✓ `verdict` MUST be APPROVE/MODIFY/REJECT  
✓ `confidence` MUST be 0.0-1.0

## That's It!

Orchestrator handles everything else.
