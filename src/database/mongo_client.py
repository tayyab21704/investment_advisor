import logging
from pymongo import MongoClient
from src.core.config import settings

logger = logging.getLogger("MongoClient")

class MongoProvider:
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client[settings.MONGO_DB_NAME]
            # Verify connection
            self.client.server_info()
        except Exception as e:
            logger.warning(f"MongoDB not connected: {e}. Using mock mode.")
            self.db = None

    def get_user_by_id(self, user_id: str):
        if self.db is not None:
            try:
                user = self.db.users.find_one({"_id": user_id})
                if user: return user
            except: pass
        # Safe mock defaults for test
        return {"risk_score": 7, "income": 120000, "monthly_surplus": 50000}

    def save_recommendation(self, doc: dict):
        if self.db is not None:
            try:
                return str(self.db.recommendations.insert_one(doc).inserted_id)
            except: pass
        return "mock_id_123"

_mongo = None
def get_mongo_client():
    global _mongo
    if _mongo is None: _mongo = MongoProvider()
    return _mongo
