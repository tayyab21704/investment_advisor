import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "investment_ai_db")
        self.client = None
        self.db = None

    def connect(self):
        try:
            self.client = MongoClient(self.uri)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            self.db = self.client[self.db_name]
            print("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")

    def get_user_profile(self, user_id: str):
        if not self.db:
            self.connect()
        
        # Line 28: Fetch user data logic
        user_collection = self.db["users"]
        return user_collection.find_one({"user_id": user_id})

# Singleton instance
mongo_client = MongoDBClient()