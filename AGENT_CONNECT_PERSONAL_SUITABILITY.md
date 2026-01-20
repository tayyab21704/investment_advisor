# Personal Suitability Agent - Connection Guide

## What This Agent Does

Determines if this investment fits the user's personal situation, goals, and portfolio.

## Input Received

```python
{
    "user_profile": UserProfile,        # User goals, horizon, situation
    "asset_candidate": AssetCandidate,  # Asset type, sector
    "position": Position                # Investment amount, % of portfolio
}
```

## What To Return

Must return `AgentOutput`:

```python
from src.orchestrator.state import AgentOutput

AgentOutput(
    agent_name="personal_suitability",
    verdict="APPROVE",              # or MODIFY, REJECT
    confidence=0.88,                # 0.0 to 1.0
    key_findings=[
        "Portfolio fit score: 0.85",
        "Time horizon: 120 months (sufficient)",
        "Position size: 15% of portfolio (good)"
    ],
    blocking_issues=[],             # Empty if no issues
    recommendations=[
        "Diversify across sectors",
        "Rebalance quarterly",
        "Monitor against goals"
    ],
    reasoning="""Suitability Analysis:
    1. Checked user financial goals
    2. Verified investment horizon
    3. Assessed portfolio impact
    4. Decision: GOOD FIT""",
    metrics={
        "fit_score": 0.85,
        "diversification_impact": 0.2,
        "tax_efficiency": 0.75
    }
)
```

## How To Connect

### Step 1: Build Your Agent Function

```python
# src/agents/suitability_agent.py
from src.orchestrator.state import AgentOutput

def check_suitability(agent_input: dict) -> AgentOutput:
    user = agent_input.get("user_profile", {})
    asset = agent_input.get("asset_candidate", {})
    position = agent_input.get("position", {})

    # YOUR LOGIC: Does this fit the investor?
    fit_score = calculate_fit(user, asset)
    time_horizon_ok = user.get("investment_horizon_months", 0) >= 36
    position_size_ok = position.get("percentage_of_portfolio", 0) <= 0.20

    # All good?
    verdict = "APPROVE" if (fit_score > 0.75 and time_horizon_ok) else "MODIFY"

    return AgentOutput(
        agent_name="personal_suitability",
        verdict=verdict,
        confidence=0.85,
        key_findings=[
            f"Fit score: {fit_score}",
            f"Time horizon: {user.get('investment_horizon_months')} months",
            f"Position: {position.get('percentage_of_portfolio')*100:.0f}%"
        ],
        blocking_issues=[] if time_horizon_ok else ["Horizon too short"],
        recommendations=["Align with goals", "Diversify", "Monitor"],
        reasoning="Your suitability assessment here",
        metrics={
            "fit_score": fit_score,
            "diversification_impact": 0.2,
            "tax_efficiency": 0.8
        }
    )
```

### Step 2: Register with Orchestrator

```python
from src.orchestrator import Orchestrator
from src.agents.suitability_agent import check_suitability

orchestrator = Orchestrator()
orchestrator.register_agent("personal_suitability", check_suitability)
```

### Step 3: Done

Orchestrator will:

1. Pass user + asset + position data
2. Call your function
3. Use your fit assessment in decision
4. Include your reasoning in AI evaluation

## Key Requirements

✓ Function name can be anything  
✓ Must accept `dict` input  
✓ Must return exactly `AgentOutput` format  
✓ Must include `reasoning` field  
✓ `agent_name` MUST be "personal_suitability"  
✓ `verdict` MUST be APPROVE/MODIFY/REJECT  
✓ `confidence` MUST be 0.0-1.0

## Purpose

You check: Is this right for THIS investor at THIS time? Does it fit their life?

## That's It!
