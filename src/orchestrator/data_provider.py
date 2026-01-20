"""
Data provider interface for orchestrator.

Defines the DataProvider protocol that all data sources must implement.
"""

from typing import Protocol
from src.orchestrator.state import UserProfile, AssetCandidate, MarketContext


class DataProvider(Protocol):
    """
    Protocol for external data sources (MongoDB, SQL, API, etc.).
    
    Any class implementing these methods can be used as a data provider.
    """
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """Load user profile from external source."""
        ...
    
    def get_asset_candidate(self, asset_id: str) -> AssetCandidate:
        """Load asset candidate from external source."""
        ...
    
    def get_market_context(self) -> MarketContext:
        """Load current market context from external source."""
        ...


def get_data_provider(provider_type: str = "mock") -> DataProvider:
    """
    Factory function to get a data provider instance.
    
    Args:
        provider_type: Type of provider ("mock" or "mongodb")
        
    Returns:
        DataProvider instance
    """
    if provider_type == "mongodb":
        from src.orchestrator.mongodb_provider import MongoDBDataProvider
        return MongoDBDataProvider()
    else:  # Default to mock
        from src.orchestrator.mongodb_provider import MongoDBDataProviderMock
        return MongoDBDataProviderMock()
