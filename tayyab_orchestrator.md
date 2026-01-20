# Tayyab's Orchestrator - How It Works

Complete explanation of each component in the Investment Council orchestrator.

---

## OVERVIEW

The orchestrator is a **multi-agent debate system** that makes investment decisions. Here's the flow:

```
1. LOAD DATA
   User Profile + Asset + Market Context (from MongoDB)
   ↓
2. CALL AGENTS
   Risk, Devil's Advocate, Personal Suitability agents analyze data
   ↓
3. COLLECT OUTPUTS
   Each agent returns verdict + reasoning + confidence
   ↓
4. AI DECIDES
   AI engine reads all reasoning and decides: Continue or Stop debate?
   ↓
5. RETURN RESULT
   Final investment recommendation
```

---

## FILE BREAKDOWN

### 1. **state.py** (Type Definitions)

**Purpose**: Defines all data structures using TypedDict (Python type-safe dictionaries).

**Key Classes**:

- **AgentOutput** - What every agent must return:
  - `agent_name`: Name of agent (string)
  - `verdict`: APPROVE / MODIFY / REJECT
  - `confidence`: 0.0 to 1.0 (how sure they are)
  - `key_findings`: List of important points
  - `blocking_issues`: Deal-breakers (if any)
  - `recommendations`: What to do next
  - `reasoning`: Detailed logic explaining their decision
  - `metrics`: Agent-specific numbers/data

- **UserProfile** - Who is investing:
  - Income, expenses, savings
  - Risk tolerance (LOW/MEDIUM/HIGH)
  - Investment goals (WEALTH, RETIREMENT, etc.)
  - Existing portfolio holdings

- **AssetCandidate** - What asset to invest in:
  - Asset ID, name, type (STOCK/BOND/etc)
  - Sector, region, liquidity class
  - Expected return percentage

- **MarketContext** - Current market conditions:
  - Market trend (BULL/BEAR/SIDEWAYS)
  - Volatility index
  - Interest rate regime
  - Macro risk level

- **Position** - The investment being considered:
  - Amount in dollars
  - Percentage of portfolio

- **CouncilState** - Complete conversation state:
  - All 5 data inputs above
  - Agent outputs (once they report)
  - Iteration count
  - Final decision

**Why it exists**: Enforces that all agents speak the same "language" - consistent data format.

---

### 2. **mongodb_provider.py** (Data Loading)

**Purpose**: Loads user/asset/market data from MongoDB (or returns test data).

**Two Classes**:

1. **MongoDBDataProvider** - Real database connection:

   ```python
   provider = MongoDBDataProvider(mongo_uri="...", db_name="investment_council")
   ```

   - Connects to MongoDB with timeout handling
   - `get_user_profile(user_id)` → fetches from `users` collection
   - `get_asset_candidate(asset_id)` → fetches from `assets` collection
   - `get_market_context()` → fetches latest from `market` collection (sorted by timestamp)
   - Converts database documents to TypedDict format

2. **MongoDBDataProviderMock** - Test data (no database needed):
   ```python
   provider = MongoDBDataProviderMock()
   ```

   - Returns hardcoded sample data
   - Useful for development without MongoDB running
   - Same interface as real provider

**Key Methods**:

- `get_user_profile()` - Returns UserProfile TypedDict
- `get_asset_candidate()` - Returns AssetCandidate TypedDict
- `get_market_context()` - Returns MarketContext TypedDict

**Why it exists**: Separates data loading from orchestrator logic. Easy to swap MongoDB for API or CSV.

---

### 3. **data_provider.py** (Interface/Factory)

**Purpose**: Defines the contract all data providers must follow + factory to create them.

**DataProvider Protocol**:

```python
class DataProvider(Protocol):
    def get_user_profile(user_id: str) → UserProfile
    def get_asset_candidate(asset_id: str) → AssetCandidate
    def get_market_context() → MarketContext
```

**Factory Function**:

```python
provider = get_data_provider("mock")      # Returns MongoDBDataProviderMock
provider = get_data_provider("mongodb")   # Returns real MongoDBDataProvider
```

**Why it exists**: Defines the "contract" - any provider must implement these 3 methods. Allows swapping implementations.

---

### 4. **orchestrator.py** (Main Engine)

**Purpose**: The core orchestrator that manages the entire debate.

**Class: Orchestrator**

**Initialization**:

```python
orchestrator = Orchestrator(
    max_iterations=5,           # Max debate rounds
    ai_engine=ai_engine_or_none,  # AI for smart decisions
    data_provider=provider        # MongoDB or mock
)
```

**Key Methods**:

1. **`register_agent(name, function)`** - Add an agent to the council

   ```python
   orchestrator.register_agent("risk_qualification", risk_agent_function)
   ```

   - Stores agents in dictionary
   - Agents are just functions that take input and return AgentOutput

2. **`initialize_state(user_id, asset_id, amount, pct)`** - Load data and create state

   ```python
   state = orchestrator.initialize_state("user_123", "AAPL", 50000, 0.15)
   ```

   - Fetches user/asset/market from data provider
   - Creates initial CouncilState
   - Returns state ready for debate

3. **`orchestrate(user_profile, asset_candidate, market_context, position)`** - Run the debate

   ```python
   final_state = orchestrator.orchestrate(state["user_profile"], ...)
   ```

   - Main loop: calls agents until decision reached
   - Iteration 1: All agents analyze
   - AI decides: continue or stop?
   - If continue: iterate again
   - If stop: return final state

4. **`call_agents(state)`** - Execute all registered agents
   - Prepares custom input for each agent (only data they need)
   - Calls each agent function
   - Stores outputs in state

5. **`evaluate_and_decide(state)`** - Use AI to decide next action
   - Passes all agent reasoning to AI engine
   - AI returns: REITERATE (keep debating) or TERMINATE (done)
   - Updates state with decision

6. **`get_final_recommendation(state)`** - Extract the final answer
   - Collects all agent verdicts
   - Returns recommendation object

**Agent Inputs** (what each agent receives):

- `risk_qualification`: user_profile, asset, market, position
- `devils_advocate`: asset, market, risk_qualification_output
- `personal_suitability`: user_profile, asset, position

**Why it exists**: Orchestrates the whole debate - loads data, calls agents, makes decisions, iterates.

---

### 5. **termination_rules.py** (Decision Logic)

**Purpose**: Decides when to stop debating and what to do.

**Main Functions**:

1. **`evaluate_council(state)`** - Rules-based evaluation (fallback):
   - Any REJECT? → REITERATE (keep debating)
   - Any blocking issues? → REITERATE
   - Low confidence? → REITERATE
   - Otherwise → TERMINATE (consensus reached)

2. **`evaluate_with_ai_engine(ai_engine, state, user_profile, asset)`** - AI-based evaluation:
   - Reads all agent outputs + their reasoning logic boxes
   - Sends to AI engine with full context
   - AI decides: REITERATE or TERMINATE?
   - AI explains why
   - Returns decision with AI reasoning

3. **`should_terminate(state)`** - Check if orchestrator should stop:
   - Hard limit: max iterations reached?
   - Evaluation result says terminate?
   - Return True/False

**Return Format**:

```python
{
    "action": "TERMINATE",  # or REITERATE
    "reason": "CONSENSUS",  # why
    "details": {...}        # additional info
}
```

**Why it exists**: Separate decision logic from orchestrator. Easy to understand when debate ends.

---

### 6. **ai_integration.py** (AI Engine Connection)

**Purpose**: Loads and uses external AI (Gemini, OpenAI) for intelligent decisions.

**Main Functions**:

1. **`load_ai_engine_from_env()`** - Load AI from .env file:

   ```python
   ai_engine = load_ai_engine_from_env()
   ```

   - Reads `AI_ENGINE_TYPE` from environment
   - Reads API key (`GEMINI_API_KEY` or `OPENAI_API_KEY`)
   - Creates and returns AI engine instance
   - Returns None if not configured

2. **`evaluate_with_ai(ai_engine, outputs, user_profile, asset, iteration, max_iterations)`** - Ask AI to decide:
   - Builds prompt with all agent reasoning
   - Sends to AI: "Should we continue debating or proceed with investment?"
   - AI responds with decision + explanation
   - Returns structured result

**How it works**:

1. Orchestrator collects all agent outputs
2. AI integration formats them with reasoning
3. Sends to Gemini or OpenAI API
4. Parses AI response (expects JSON)
5. Returns decision to orchestrator

**Why it exists**: Separates AI connection from orchestrator. Easy to change AI providers.

---

### 7. ****init**.py** (Public API)

**Purpose**: Exports all public classes and functions.

**What's exported**:

- `Orchestrator` - Main class
- `CouncilState`, `AgentOutput`, `UserProfile`, etc. - Data types
- `DataProvider`, `MongoDBDataProvider`, `MongoDBDataProviderMock` - Data loading
- `evaluate_council`, `should_terminate`, `evaluate_with_ai_engine` - Decision logic
- `load_ai_engine_from_env` - AI loading

**Usage**:

```python
from src.orchestrator import Orchestrator, AgentOutput, MongoDBDataProvider
```

**Why it exists**: Clean public API. Users don't need to know internal file structure.

---

## HOW TO USE

### Step 1: Setup

```python
from src.orchestrator import Orchestrator, MongoDBDataProviderMock
from src.config.llm_config import GeminiAIEngine

# Create AI engine (or load from .env)
ai_engine = GeminiAIEngine(api_key="your_key")

# Create data provider
data_provider = MongoDBDataProviderMock()  # or MongoDBDataProvider for real DB

# Create orchestrator
orchestrator = Orchestrator(
    max_iterations=5,
    ai_engine=ai_engine,
    data_provider=data_provider
)
```

### Step 2: Register Agents

```python
from src.agents.risk_agent import analyze_risk
from src.agents.devils_advocate import challenge_decision
from src.agents.suitability_agent import check_fit

orchestrator.register_agent("risk_qualification", analyze_risk)
orchestrator.register_agent("devils_advocate", challenge_decision)
orchestrator.register_agent("personal_suitability", check_fit)
```

### Step 3: Initialize State

```python
state = orchestrator.initialize_state(
    user_id="user_123",
    asset_id="AAPL",
    proposed_investment_amount=50000.0,
    percentage_of_portfolio=0.15
)
```

### Step 4: Run Debate

```python
final_state = orchestrator.orchestrate(
    user_profile=state["user_profile"],
    asset_candidate=state["asset_candidate"],
    market_context=state["market_context"],
    position=state["position"]
)
```

### Step 5: Get Result

```python
recommendation = orchestrator.get_final_recommendation(final_state)
# Output: {"risk_qualification": "APPROVE", "devils_advocate": "MODIFY", ...}
```

---

## ENVIRONMENT VARIABLES

Create `.env` file:

```
# AI Engine Configuration
AI_ENGINE_TYPE=gemini        # or openai
GEMINI_API_KEY=your_key      # Google Gemini API key
OPENAI_API_KEY=your_key      # OpenAI API key

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=investment_council
```

---

## DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    START ORCHESTRATION                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   Load Data Provider    │
              │  (MongoDB or Mock)      │
              └────────────┬────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Initialize State                  │
         │  - Fetch UserProfile               │
         │  - Fetch AssetCandidate            │
         │  - Fetch MarketContext             │
         │  - Create Position                 │
         └─────────────────┬──────────────────┘
                           │
        ┌──────────────────▼───────────────────┐
        │  DEBATE LOOP (max_iterations)        │
        │  ├─ Iteration 1                      │
        │  ├─ Iteration 2                      │
        │  └─ ...                              │
        │                                      │
        │  Each iteration:                     │
        │  1. Call all agents                  │
        │  2. Collect outputs                  │
        │  3. AI reads reasoning               │
        │  4. AI decides: REITERATE/TERMINATE  │
        │  5. If TERMINATE → Exit loop         │
        └──────────────────┬───────────────────┘
                           │
              ┌────────────▼────────────┐
              │  Extract Final Result   │
              │  (all verdicts)         │
              └────────────┬────────────┘
                           │
        ┌──────────────────▼───────────────────┐
        │  RETURN Final State to User          │
        └──────────────────────────────────────┘
```

---

## KEY CONCEPTS

**TypedDict**: Python type system for dictionaries. Ensures all data has required fields.

**Protocol**: Interface definition. Says "any data provider must have these methods."

**Agent**: Just a function that takes input dict → returns AgentOutput dict.

**State**: Dictionary containing all debate conversation data.

**Iteration**: One round where all agents analyze and AI decides.

**Reasoning**: Each agent explains WHY they made their decision.

**AI Engine**: External service (Gemini/OpenAI) that reads reasoning and decides intelligently.

---

## CLEAN ARCHITECTURE

- **state.py** - No dependencies, pure data structures ✓
- **data_provider.py** - Defines interface, no business logic ✓
- **mongodb_provider.py** - Implements interface, handles MongoDB only ✓
- **ai_integration.py** - Handles AI connection only ✓
- **termination_rules.py** - Decision logic only ✓
- **orchestrator.py** - Orchestrates above components ✓

Each file has one job. Easy to test. Easy to replace (e.g., swap MongoDB for API).
