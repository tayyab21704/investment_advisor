# How to Connect Agents to Orchestrator - Master Guide

## 3 Agents You Need to Build

1. **Risk Qualification** - Does risk fit user tolerance?
2. **Devil's Advocate** - What could go wrong?
3. **Personal Suitability** - Does this fit the investor?

---

## Quick Summary (For Each Agent)

### Agent Contract (ALL must do this)

```python
from src.orchestrator.state import AgentOutput

def your_agent_function(agent_input: dict) -> AgentOutput:
    # Extract inputs
    data = agent_input.get("field_name")

    # YOUR LOGIC HERE
    analysis = analyze_something(data)
    verdict = decide_verdict(analysis)

    # RETURN THIS FORMAT
    return AgentOutput(
        agent_name="agent_name",           # MUST match registration
        verdict=verdict,                    # APPROVE/MODIFY/REJECT
        confidence=0.85,                    # 0.0 to 1.0
        key_findings=["Point 1", "Point 2"],
        blocking_issues=[],
        recommendations=["Suggestion 1"],
        reasoning="Explain your logic here",
        metrics={"key": value}
    )
```

---

## Step-by-Step to Connect

### 1. Build Your Agent Function

Location: `src/agents/your_agent.py`

- Accept dict input
- Return AgentOutput
- Include detailed reasoning

### 2. Import in Your Code

```python
from src.agents.your_agent import your_function
```

### 3. Register with Orchestrator

```python
from src.orchestrator import Orchestrator

orchestrator = Orchestrator()
orchestrator.register_agent("risk_qualification", risk_function)
orchestrator.register_agent("devils_advocate", devils_function)
orchestrator.register_agent("personal_suitability", suitability_function)
```

### 4. Initialize and Run

```python
state = orchestrator.initialize_state("user_id", "asset_id", 50000, 0.15)
final_state = orchestrator.orchestrate(
    user_profile=state["user_profile"],
    asset_candidate=state["asset_candidate"],
    market_context=state["market_context"],
    position=state["position"]
)
recommendation = orchestrator.get_final_recommendation(final_state)
```

---

## Input/Output for Each Agent

### Risk Qualification Agent

**Inputs:** user_profile, asset_candidate, market_context, position  
**Purpose:** Risk analysis  
**Outputs:** Verdict on risk tolerance fit

### Devil's Advocate Agent

**Inputs:** asset_candidate, market_context, risk_qualification (output)  
**Purpose:** Challenge the decision, find risks  
**Outputs:** Contrarian perspective

### Personal Suitability Agent

**Inputs:** user_profile, asset_candidate, position  
**Purpose:** Check if investment fits investor's life  
**Outputs:** Suitability verdict

---

## Full AgentOutput Fields

| Field           | Type  | Required | Example                       |
| --------------- | ----- | -------- | ----------------------------- |
| agent_name      | str   | YES      | "risk_qualification"          |
| verdict         | str   | YES      | "APPROVE" (or MODIFY, REJECT) |
| confidence      | float | YES      | 0.85                          |
| key_findings    | list  | YES      | ["Finding 1", "Finding 2"]    |
| blocking_issues | list  | YES      | [] or ["Issue"]               |
| recommendations | list  | YES      | ["Action 1"]                  |
| reasoning       | str   | YES      | "Why I decided this..."       |
| metrics         | dict  | YES      | {"score": 0.8}                |

---

## What Orchestrator Does

1. Calls all agents with their specific inputs
2. Collects AgentOutput from each
3. Passes all reasoning to AI engine
4. AI reads reasoning + decides: REITERATE (keep debating) or TERMINATE (done)
5. If TERMINATE → returns recommendation
6. If REITERATE → runs all agents again

---

## Important Notes

✓ Your function name doesn't matter  
✓ agent_name in output MUST match registration name  
✓ All fields REQUIRED in AgentOutput  
✓ reasoning field is read by AI engine  
✓ Orchestrator passes ONLY required inputs to each agent  
✓ Agents are stateless (no side effects)  
✓ Agents never see each other's outputs

---

## For Detailed Info on Each Agent

See separate files:

- `AGENT_CONNECT_RISK_QUALIFICATION.md` - Risk agent details
- `AGENT_CONNECT_DEVILS_ADVOCATE.md` - Devil's advocate details
- `AGENT_CONNECT_PERSONAL_SUITABILITY.md` - Suitability agent details

---

## Example: Complete Setup

```python
from src.orchestrator import Orchestrator
from src.agents.risk_agent import analyze_risk
from src.agents.devils_agent import challenge_decision
from src.agents.suitability_agent import check_fit

# Create orchestrator
orchestrator = Orchestrator(max_iterations=5)

# Register agents
orchestrator.register_agent("risk_qualification", analyze_risk)
orchestrator.register_agent("devils_advocate", challenge_decision)
orchestrator.register_agent("personal_suitability", check_fit)

# Load data
state = orchestrator.initialize_state("user_123", "AAPL", 50000, 0.15)

# Run debate
final = orchestrator.orchestrate(
    user_profile=state["user_profile"],
    asset_candidate=state["asset_candidate"],
    market_context=state["market_context"],
    position=state["position"]
)

# Get result
result = orchestrator.get_final_recommendation(final)
print(result)
# Output: {"risk_qualification": "APPROVE", "devils_advocate": "MODIFY", ...}
```

That's it. Your agents are connected!
