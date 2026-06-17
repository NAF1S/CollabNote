import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_NAME = os.getenv("DATABASE_NAME", "mongodb")


class MongoDBManager:
    """Manage MongoDB connections for the consumer."""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.client[MONGODB_NAME]
        print(f"Consumer connected to MongoDB: {MONGODB_NAME}")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("Consumer disconnected from MongoDB")
    
    async def insert_activity_log(self, event: dict) -> bool:
        """
        Insert an activity log document into MongoDB.
        
        Args:
            event: Event dict with event_type, user_id, resource_id, timestamp, metadata
        
        Returns:
            True if inserted successfully, False otherwise
        """
        try:
            result = await self.db.activity_logs.insert_one(event)
            print(f"Activity logged: {event['event_type']} for user {event['user_id']}")
            return True
        except Exception as e:
            print(f"Failed to insert activity log: {e}")
            return False
