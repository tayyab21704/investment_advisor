# Devil's Advocate Agent - Connection Guide

## What This Agent Does

Plays devil's advocate - challenges consensus and points out risks others miss.

## Input Received

```python
{
    "asset_candidate": AssetCandidate,       # Asset being evaluated
    "market_context": MarketContext,         # Market conditions
    "risk_qualification": AgentOutput        # Risk agent output (for context)
}
```

## What To Return

Must return `AgentOutput`:

```python
from src.orchestrator.state import AgentOutput

AgentOutput(
    agent_name="devils_advocate",
    verdict="MODIFY",               # or APPROVE, REJECT
    confidence=0.72,                # 0.0 to 1.0
    key_findings=[
        "Market may be overheated",
        "Contrarian signals detected",
        "Regulatory risks unpriced"
    ],
    blocking_issues=[],             # Raise if critical
    recommendations=[
        "Reduce position size",
        "Hedge downside",
        "Monitor economic data"
    ],
    reasoning="""Devil's Advocate Analysis:
    1. Assessed market sentiment
    2. Identified contrarian signals
    3. Found tail risk factors
    4. Decision: CAUTION NEEDED""",
    metrics={
        "euphoria_level": 0.72,
        "contrarian_index": 65,
        "tail_risk_multiplier": 1.5
    }
)
```

## How To Connect

### Step 1: Build Your Agent Function

```python
# src/agents/devils_advocate_agent.py
from src.orchestrator.state import AgentOutput

def challenge_decision(agent_input: dict) -> AgentOutput:
    asset = agent_input.get("asset_candidate", {})
    market = agent_input.get("market_context", {})
    risk_output = agent_input.get("risk_qualification", {})

    # YOUR LOGIC: Find risks others missed
    market_euphoria = assess_market_sentiment(market)
    contrarian_signals = find_contrarian_signals(asset, market)
    tail_risks = calculate_tail_risks(asset)

    # Should we be cautious?
    verdict = "MODIFY" if market_euphoria > 0.7 else "APPROVE"

    return AgentOutput(
        agent_name="devils_advocate",
        verdict=verdict,
        confidence=0.80,
        key_findings=["Market euphoria: 0.72", "Signals found"],
        blocking_issues=[],
        recommendations=["Consider hedging", "Monitor risks"],
        reasoning="Your contrarian analysis here",
        metrics={
            "euphoria": market_euphoria,
            "contrarian_index": contrarian_signals,
            "tail_risk": tail_risks
        }
    )
```

### Step 2: Register with Orchestrator

```python
from src.orchestrator import Orchestrator
from src.agents.devils_advocate_agent import challenge_decision

orchestrator = Orchestrator()
orchestrator.register_agent("devils_advocate", challenge_decision)
```

### Step 3: Done

Orchestrator will:

1. Pass asset + market data
2. Call your function
3. Use your reasoning in AI decision
4. Your verdict influences final recommendation

## Key Requirements

✓ Function name can be anything  
✓ Must accept `dict` input  
✓ Must return exactly `AgentOutput` format  
✓ Must include `reasoning` field  
✓ `agent_name` MUST be "devils_advocate"  
✓ `verdict` MUST be APPROVE/MODIFY/REJECT  
✓ `confidence` MUST be 0.0-1.0

## Purpose

You're the skeptic - question assumptions, find blind spots, warn about risks.

## That's It!
