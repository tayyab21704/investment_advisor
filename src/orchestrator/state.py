"""
CouncilState and AgentOutput type definitions.

This is the CANONICAL, FINAL specification for all agents in the AI Investment Council.
Every agent must follow this contract exactly.

Reference: FINAL_AGENT_SPECIFICATION.md
"""

from typing import TypedDict, Literal, Optional


# ============================================================================
# 1. UNIVERSAL AGENT OUTPUT (MANDATORY FOR ALL AGENTS)
# ============================================================================

class AgentOutput(TypedDict):
    """
    MANDATORY output structure for ALL agents.
    
    Every agent MUST return exactly this format.
    The orchestrator ONLY reads these fields.
    """
    agent_name: str
    verdict: Literal["APPROVE", "MODIFY", "REJECT"]
    confidence: float  # 0.0 to 1.0
    key_findings: list[str]
    blocking_issues: list[str]
    recommendations: list[str]
    reasoning: str  # Agent's reasoning/logic box explaining their analysis
    metrics: dict  # Agent-specific - see agent docs


# ============================================================================
# 2. GLOBAL STATE (READ-ONLY FOR AGENTS)
# ============================================================================

class UserProfile(TypedDict, total=False):
    """User investment profile and constraints (from MongoDB or external)."""
    monthly_income: float
    monthly_expenses: float
    total_savings: float
    existing_investments: list[dict]
    risk_tolerance: Literal["LOW", "MEDIUM", "HIGH"]
    investment_horizon_months: int
    financial_goals: list[Literal["WEALTH", "RETIREMENT", "INCOME", "CAPITAL_PRESERVATION"]]


class AssetCandidate(TypedDict, total=False):
    """Asset being evaluated (from MongoDB or external)."""
    asset_id: str
    asset_name: str
    asset_type: Literal["STOCK", "ETF", "BOND", "CRYPTO", "COMMODITY"]
    sector: str
    region: str
    liquidity_class: Literal["HIGH", "MEDIUM", "LOW"]
    expected_return_pct: float


class MarketContext(TypedDict, total=False):
    """Current market conditions (from MongoDB or external)."""
    market_trend: Literal["BULL", "BEAR", "SIDEWAYS"]
    volatility_index: float
    interest_rate_regime: Literal["RISING", "STABLE", "FALLING"]
    macro_risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class Position(TypedDict, total=False):
    """Position sizing information (from MongoDB or external)."""
    proposed_investment_amount: float
    percentage_of_portfolio: float


class CouncilState(TypedDict, total=False):
    """
    Global council state - SINGLE SOURCE OF TRUTH.
    
    This state is read by agents and maintained by the orchestrator.
    Each iteration, agent outputs are added to this state.
    
    AGENTS READ FROM: user_profile, asset_candidate, market_context, position, 
                      previous agent outputs, iteration
    AGENTS WRITE TO: their own output namespace only
    """
    # ─────────────────────────────────────────────────────────────────────
    # IMMUTABLE INPUTS (Set once from MongoDB/external source)
    # ─────────────────────────────────────────────────────────────────────
    user_profile: UserProfile
    asset_candidate: AssetCandidate
    market_context: MarketContext
    position: Position
    
    # ─────────────────────────────────────────────────────────────────────
    # AGENT OUTPUTS (Updated after each agent runs)
    # ─────────────────────────────────────────────────────────────────────
    risk_qualification: Optional[AgentOutput]  # Risk Qualification Agent output
    devils_advocate: Optional[AgentOutput]      # Devil's Advocate Agent output
    personal_suitability: Optional[AgentOutput] # Personal Suitability Agent output
    
    # ─────────────────────────────────────────────────────────────────────
    # ORCHESTRATOR METADATA
    # ─────────────────────────────────────────────────────────────────────
    iteration: int
    decision: Optional[dict]
    max_iterations: int
    debate_history: list[dict]


# ============================================================================
# 3. EVALUATION RESULT (ORCHESTRATOR DECISION)
# ============================================================================

class EvaluationResult(TypedDict):
    """Result of orchestrator evaluation."""
    action: Literal["TERMINATE", "REITERATE"]
    reason: str
    details: dict


# ============================================================================
# 4. FINAL INVESTMENT VERDICT (OUTPUT FROM ORCHESTRATION)
# ============================================================================

class FinalVerdict(TypedDict):
    """Final recommendation after orchestration complete."""
    final_verdict: Literal["INVEST", "DO_NOT_INVEST"]
    confidence: float
    asset: AssetCandidate
    position: Position
    risk_summary: dict
    suitability_summary: dict
    warnings: list[str]
