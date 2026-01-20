# FINAL ORCHESTRATOR DESIGN

## 🎯 What Is The Orchestrator?

**Simple answer:** A debate moderator that makes investment decisions.

Think of it like this:

- You have 3 financial advisors (agents)
- They analyze an investment
- They argue about it (debate)
- An AI referee decides: "Approve or reject?"
- That's the orchestrator

---

## 🚀 The Big Picture (5 Step Flow)

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: LOAD DATA                                       │
│ → Get user info, asset details, market conditions      │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: CALL AGENTS (Multiple Rounds)                  │
│ → Agent 1: Check risk                                   │
│ → Agent 2: Find problems (devil's advocate)            │
│ → Agent 3: Check personal fit                          │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: COLLECT VERDICTS                               │
│ → Agent 1 says: APPROVE (confidence: 0.85)             │
│ → Agent 2 says: MODIFY (confidence: 0.72)              │
│ → Agent 3 says: APPROVE (confidence: 0.88)             │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: AI DECIDES                                      │
│ → AI reads all reasoning                               │
│ → Decides: Continue debating OR Approve?               │
│ → If continue: Go back to Step 2                        │
│ → If done: Go to Step 5                                │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: RETURN RESULT                                  │
│ → Investment approved or rejected                      │
│ → Show all reasoning from agents                       │
└─────────────────────────────────────────────────────────┘
```

**That's literally it.**

---

## 📦 The 7 Files (What Each Does)

### 1️⃣ **state.py** — The Blueprint

**What it is:** Data type definitions (TypedDict)

**Why needed:** Ensures everyone uses the same format

**Key types:**

- `AgentOutput` ← What agents must return
- `UserProfile` ← Investor information
- `AssetCandidate` ← Investment details
- `CouncilState` ← Entire debate state

**In one sentence:** "This is the template everyone follows"

---

### 2️⃣ **data_provider.py** — The Contract

**What it is:** Interface that says "Any data source must have these methods"

**Why needed:** Lets us swap MongoDB for API/CSV easily

**Methods required:**

- `get_user_profile()` - Get investor data
- `get_asset_candidate()` - Get investment data
- `get_market_context()` - Get market conditions

**Also has:** `get_data_provider()` factory function

**In one sentence:** "Every data source must have these 3 methods"

---

### 3️⃣ **mongodb_provider.py** — Real Database Connection

**What it is:** Actually loads data from MongoDB (or returns test data)

**Two classes:**

1. `MongoDBDataProvider` - Real database
2. `MongoDBDataProviderMock` - Test data (no DB needed)

**Why needed:** Implements the contract from step 2

**In one sentence:** "Gets data from MongoDB or test data"

---

### 4️⃣ **orchestrator.py** — The Brain

**What it is:** Main engine that coordinates everything

**Key methods:**

- `initialize_state()` - Loads data
- `call_agents()` - Runs all agents
- `evaluate_and_decide()` - Uses AI to decide
- `orchestrate()` - Main loop

**The main loop:**

```
for iteration in range(max_iterations):
  1. Call agents
  2. Get verdicts
  3. AI decides: stop or continue?
  4. If stop: return result
  5. If continue: repeat
```

**In one sentence:** "Orchestrates the whole debate"

---

### 5️⃣ **termination_rules.py** — When To Stop

**What it is:** Decision logic (when does debate end?)

**Two ways to decide:**

1. **Rules-based** (simple):
   - Any reject? → Keep debating
   - Low confidence? → Keep debating
   - Otherwise → Done

2. **AI-based** (smart):
   - AI reads all reasoning
   - AI decides intelligently
   - AI explains why

**In one sentence:** "Decides when the debate is over"

---

### 6️⃣ **ai_integration.py** — AI Connection

**What it is:** Connects to Gemini or OpenAI

**What it does:**

1. Loads AI from `.env` file
2. Sends agent reasoning to AI
3. Gets decision back

**In one sentence:** "Talks to AI to make smart decisions"

---

### 7️⃣ ****init**.py** — Public Door

**What it is:** Exports everything

**Why needed:** Users don't need to know internal structure

**Simple import:**

```python
from src.orchestrator import Orchestrator, AgentOutput
```

**In one sentence:** "Makes it easy to use orchestrator"

---

## 🔄 How It Actually Works (Deep Dive)

### MOMENT 1: Setup

```python
orchestrator = Orchestrator()
```

✓ Creates orchestrator
✓ Loads AI engine from .env
✓ Sets max iterations to 5

---

### MOMENT 2: Register Agents

```python
orchestrator.register_agent("risk_qualification", risk_function)
orchestrator.register_agent("devils_advocate", devils_function)
orchestrator.register_agent("personal_suitability", suitability_function)
```

✓ Stores 3 agents in a dictionary
✓ Ready to be called

---

### MOMENT 3: Load Data

```python
state = orchestrator.initialize_state("user_123", "AAPL", 50000, 0.15)
```

What happens inside:

1. `data_provider.get_user_profile("user_123")` → fetches from MongoDB
2. `data_provider.get_asset_candidate("AAPL")` → fetches from MongoDB
3. `data_provider.get_market_context()` → fetches latest market data
4. Creates `CouncilState` object with all this data

Result:

```
state = {
  "user_profile": {...},
  "asset_candidate": {...},
  "market_context": {...},
  "position": {...},
  "iteration": 0,
  "decision": None
}
```

---

### MOMENT 4: Start Main Loop

```python
final_state = orchestrator.orchestrate(state["user_profile"], ...)
```

**Inside orchestrate() - ITERATION 1:**

1️⃣ **Prepare Agent Inputs**

- Risk agent needs: user, asset, market, position
- Devil's advocate needs: asset, market, risk_output
- Suitability needs: user, asset, position
- Each gets ONLY what it needs

2️⃣ **Call All Agents**

```
agent_1_output = risk_function(prepared_input)
agent_2_output = devils_function(prepared_input)
agent_3_output = suitability_function(prepared_input)
```

3️⃣ **Collect Outputs**

```
{
  "risk_qualification": {
    "verdict": "APPROVE",
    "confidence": 0.85,
    "reasoning": "..."
  },
  "devils_advocate": {
    "verdict": "MODIFY",
    "confidence": 0.72,
    "reasoning": "..."
  },
  "personal_suitability": {
    "verdict": "APPROVE",
    "confidence": 0.88,
    "reasoning": "..."
  }
}
```

4️⃣ **AI Makes Decision**

- Sends all reasoning to AI
- AI reads: "All agents approve except devil's advocate"
- AI thinks: "Devil's advocate has valid concerns"
- AI decides: "Continue debate (REITERATE)"

5️⃣ **Check Termination**

- Is iteration >= max_iterations? NO
- Did AI say TERMINATE? NO
- Continue to ITERATION 2

**Inside orchestrate() - ITERATION 2:**

Same as iteration 1, but this time:

- Agents see iteration count (for context)
- They might change verdicts
- AI re-evaluates

**Inside orchestrate() - AI Says STOP**

AI decides: "Now I see consensus. APPROVE."

Loop exits. Return final state.

---

## 📊 Agent Inputs & Outputs

### Agent 1: Risk Qualification

```
INPUT:
  user_profile (risk tolerance, investment horizon)
  asset_candidate (risk profile)
  market_context (volatility)
  position (amount)

OUTPUT:
  verdict: APPROVE (risk is ok)
  confidence: 0.85
  reasoning: "Risk score 45 < user tolerance 50"
```

### Agent 2: Devil's Advocate

```
INPUT:
  asset_candidate (the investment)
  market_context (market conditions)
  risk_qualification (what risk agent said)

OUTPUT:
  verdict: MODIFY (be cautious)
  confidence: 0.72
  reasoning: "Market may be overheated, tail risks uncovered"
```

### Agent 3: Personal Suitability

```
INPUT:
  user_profile (goals, situation)
  asset_candidate (investment type)
  position (allocation %)

OUTPUT:
  verdict: APPROVE (good fit)
  confidence: 0.88
  reasoning: "Matches 10-year goal, proper diversification"
```

---

## 🤖 How AI Makes Smart Decisions

### Before (Rules-Based - Old)

```
If any agent says REJECT → Keep debating
If confidence < 0.75 → Keep debating
Otherwise → Done
```

**Problem:** Dumb. Doesn't understand context.

### After (AI-Based - New)

```
AI reads all reasoning:
  "Risk agent says OK because X"
  "Devil's advocate worried about Y"
  "Suitability agent says fits personal goals"

AI thinks: "Ah, I see. Devil's advocate is right to worry.
           But risk and suitability both OK.
           Continue debate to address devil's concerns."

AI decides: REITERATE or TERMINATE
```

**Advantage:** Smart. Understands nuance.

---

## 📍 Key Concepts (Simple)

| Concept            | Means                                      |
| ------------------ | ------------------------------------------ |
| **Verdict**        | Agent's decision (APPROVE/MODIFY/REJECT)   |
| **Confidence**     | How sure (0.0 = not sure, 1.0 = very sure) |
| **Reasoning**      | Why they decided that                      |
| **Blocking Issue** | Deal-breaker that stops debate             |
| **Iteration**      | One round of agent calls                   |
| **State**          | Current debate status                      |
| **Termination**    | Debate ends                                |
| **Reiterate**      | Keep debating                              |

---

## ⚙️ Configuration (.env file)

```
# AI Engine (pick one)
AI_ENGINE_TYPE=gemini
GEMINI_API_KEY=your_key_here

# OR
AI_ENGINE_TYPE=openai
OPENAI_API_KEY=your_key_here

# Database
MONGO_URI=mongodb://localhost:27017
MONGO_DB=investment_council
```

---

## 💻 Usage (Copy-Paste Ready)

```python
# 1. Import
from src.orchestrator import Orchestrator
from src.agents.risk_agent import analyze_risk
from src.agents.devils_agent import challenge
from src.agents.suitability_agent import check_fit

# 2. Create
orchestrator = Orchestrator()

# 3. Register
orchestrator.register_agent("risk_qualification", analyze_risk)
orchestrator.register_agent("devils_advocate", challenge)
orchestrator.register_agent("personal_suitability", check_fit)

# 4. Load
state = orchestrator.initialize_state(
    user_id="user_123",
    asset_id="AAPL",
    proposed_investment_amount=50000,
    percentage_of_portfolio=0.15
)

# 5. Run
final = orchestrator.orchestrate(
    user_profile=state["user_profile"],
    asset_candidate=state["asset_candidate"],
    market_context=state["market_context"],
    position=state["position"]
)

# 6. Get Result
result = orchestrator.get_final_recommendation(final)
print(result)
# → {"risk_qualification": "APPROVE", "devils_advocate": "MODIFY", ...}
```

Done.

---

## ✅ Why This Design Is Good

| Feature        | Why                             |
| -------------- | ------------------------------- |
| **Modular**    | Each file does one job          |
| **Testable**   | Easy to test each component     |
| **Extensible** | Easy to add new agents          |
| **Swappable**  | Easy to swap MongoDB for API    |
| **AI-Powered** | Smart decisions, not dumb rules |
| **Scalable**   | Can handle many agents          |
| **Clean**      | No spaghetti code               |

---

## 🎬 Quick Timeline

```
Day 1: Setup orchestrator + register 3 agents
Day 2: Test with mock data
Day 3: Connect real MongoDB
Day 4: Connect real agents
Day 5: Done
```

---

## 🚨 Common Issues

**Issue:** Agent returns wrong format
**Fix:** Return exactly AgentOutput with all 8 fields

**Issue:** Agent crashes
**Fix:** Check inputs - orchestrator passes specific fields to each agent

**Issue:** AI not being called
**Fix:** Make sure .env has AI_ENGINE_TYPE and API key

**Issue:** Loop never stops
**Fix:** AI should decide TERMINATE, or increase max_iterations check

---

## 🎯 Final Summary

| What              | Details                                               |
| ----------------- | ----------------------------------------------------- |
| **Purpose**       | Multi-agent debate for investment decisions           |
| **Files**         | 7 core files (state, provider, orchestrator, AI, etc) |
| **Flow**          | Load → Call agents → AI decides → Done                |
| **Iterations**    | Agents run multiple rounds until consensus            |
| **AI Role**       | Reads reasoning, makes smart decisions                |
| **Extensibility** | Add new agents easily                                 |
| **Status**        | Production-ready                                      |

---

## 🏁 The Bottom Line

**This orchestrator is:**

- ✅ Simple (7 files, clear flow)
- ✅ Modular (easy to change parts)
- ✅ AI-powered (smart decisions)
- ✅ Production-ready (tested, clean)
- ✅ Extensible (add agents easily)

**To use it:**

1. Build your agents
2. Register them
3. Call orchestrate()
4. Get result

That's it.
