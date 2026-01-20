"""
MongoDB data provider for orchestrator.

Implements the DataProvider interface to load user profiles, assets, and market context
from MongoDB collections.
"""

from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

from src.orchestrator.data_provider import DataProvider
from src.orchestrator.state import UserProfile, AssetCandidate, MarketContext

logger = logging.getLogger(__name__)


class MongoDBDataProvider(DataProvider):
    """
    MongoDB implementation of DataProvider.
    
    Loads:
    - user_profile from users collection
    - asset_candidate from assets collection
    - market_context from market collection
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "investment_council",
        timeout_ms: int = 5000
    ):
        """
        Initialize MongoDB data provider.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            timeout_ms: Connection timeout in milliseconds
        """
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=timeout_ms)
            # Test connection
            self.client.server_info()
            self.db = self.client[database_name]
            logger.info(f"MongoDB connected: {database_name}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ValueError(f"MongoDB connection failed: {e}")
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Load user profile from MongoDB users collection.
        
        Args:
            user_id: User document ID
            
        Returns:
            UserProfile TypedDict
            
        Raises:
            ValueError: If user not found
        """
        try:
            doc = self.db.users.find_one({"_id": user_id})
            if not doc:
                raise ValueError(f"User {user_id} not found in MongoDB")
            
            return UserProfile(
                monthly_income=doc.get("monthly_income", 0),
                monthly_expenses=doc.get("monthly_expenses", 0),
                total_savings=doc.get("total_savings", 0),
                existing_investments=doc.get("existing_investments", []),
                risk_tolerance=doc.get("risk_tolerance", "MEDIUM"),
                investment_horizon_months=doc.get("investment_horizon_months", 60),
                financial_goals=doc.get("financial_goals", [])
            )
        except Exception as e:
            logger.error(f"Error loading user profile {user_id}: {e}")
            raise
    
    def get_asset_candidate(self, asset_id: str) -> AssetCandidate:
        """
        Load asset candidate from MongoDB assets collection.
        
        Args:
            asset_id: Asset document ID
            
        Returns:
            AssetCandidate TypedDict
            
        Raises:
            ValueError: If asset not found
        """
        try:
            doc = self.db.assets.find_one({"_id": asset_id})
            if not doc:
                raise ValueError(f"Asset {asset_id} not found in MongoDB")
            
            return AssetCandidate(
                asset_id=doc.get("_id"),
                asset_name=doc.get("asset_name", ""),
                asset_type=doc.get("asset_type", "STOCK"),
                sector=doc.get("sector", ""),
                region=doc.get("region", ""),
                liquidity_class=doc.get("liquidity_class", "MEDIUM"),
                expected_return_pct=doc.get("expected_return_pct", 0)
            )
        except Exception as e:
            logger.error(f"Error loading asset candidate {asset_id}: {e}")
            raise
    
    def get_market_context(self) -> MarketContext:
        """
        Load current market context from MongoDB market collection.
        
        Gets the most recent market snapshot.
        
        Returns:
            MarketContext TypedDict
            
        Raises:
            ValueError: If no market context found
        """
        try:
            # Get latest market document (sort by timestamp descending)
            doc = self.db.market.find_one(sort=[("timestamp", -1)])
            if not doc:
                raise ValueError("No market context found in MongoDB")
            
            return MarketContext(
                market_trend=doc.get("market_trend", "SIDEWAYS"),
                volatility_index=doc.get("volatility_index", 20.0),
                interest_rate_regime=doc.get("interest_rate_regime", "STABLE"),
                macro_risk_level=doc.get("macro_risk_level", "MEDIUM")
            )
        except Exception as e:
            logger.error(f"Error loading market context: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


class MongoDBDataProviderMock(DataProvider):
    """
    Mock MongoDB provider for testing (returns hardcoded data).
    
    Use this for development and testing without a real MongoDB.
    """
    
    def get_user_profile(self, user_id: str = "test_user") -> UserProfile:
        """Return mock user profile."""
        return UserProfile(
            monthly_income=8000,
            monthly_expenses=3500,
            total_savings=250000,
            existing_investments=[
                {"name": "US_STOCKS_INDEX", "allocation_pct": 50},
                {"name": "INT_BONDS", "allocation_pct": 30},
                {"name": "CASH", "allocation_pct": 20}
            ],
            risk_tolerance="MEDIUM",
            investment_horizon_months=120,
            financial_goals=["WEALTH", "RETIREMENT"]
        )
    
    def get_asset_candidate(self, asset_id: str = "test_asset") -> AssetCandidate:
        """Return mock asset."""
        return AssetCandidate(
            asset_id="AAPL_2026",
            asset_name="Apple Inc.",
            asset_type="STOCK",
            sector="TECHNOLOGY",
            region="US",
            liquidity_class="HIGH",
            expected_return_pct=8.5
        )
    
    def get_market_context(self) -> MarketContext:
        """Return mock market context."""
        return MarketContext(
            market_trend="BULL",
            volatility_index=16.5,
            interest_rate_regime="STABLE",
            macro_risk_level="LOW"
        )
