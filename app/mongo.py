import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGO_URL")
MONGODB_NAME = os.getenv("DATABASE_NAME")


mongo_client : AsyncIOMotorClient = None
mongodb_db = None

async def connet_to_db():
    global mongo_client,mongodb_db
    