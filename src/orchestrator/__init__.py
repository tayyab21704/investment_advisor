"""
Investment Council Orchestrator.

Core orchestration layer for multi-agent debate system with AI-based decision making.
"""

from src.orchestrator.orchestrator import Orchestrator
from src.orchestrator.state import (
    CouncilState,
    AgentOutput,
    UserProfile,
    AssetCandidate,
    MarketContext,
    Position,
    EvaluationResult,
    FinalVerdict
)
from src.orchestrator.data_provider import DataProvider
from src.orchestrator.mongodb_provider import MongoDBDataProvider, MongoDBDataProviderMock
from src.orchestrator.termination_rules import evaluate_council, should_terminate, evaluate_with_ai_engine
from src.orchestrator.ai_integration import load_ai_engine_from_env

__all__ = [
    "Orchestrator",
    "CouncilState",
    "AgentOutput",
    "UserProfile",
    "AssetCandidate",
    "MarketContext",
    "Position",
    "EvaluationResult",
    "FinalVerdict",
    "DataProvider",
    "MongoDBDataProvider",
    "MongoDBDataProviderMock",
    "evaluate_council",
    "should_terminate",
    "evaluate_with_ai_engine",
    "load_ai_engine_from_env",
]
