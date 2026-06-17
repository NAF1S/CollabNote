import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL","mongodb://localhost:27017")
MONGODB_NAME = os.getenv("DATABASE_NAME","mongodb")


mongo_client : AsyncIOMotorClient = None
mongodb_db = None

async def connect_to_mongodb():
    global mongo_client, mongodb_db
    mongo_client = AsyncIOMotorClient(MONGODB_URL)
    mongodb_db = mongo_client[MONGODB_NAME]
    print(f"Connected to MongoDB: {MONGODB_NAME}")


async def close_mongodb_connection():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("Closed MongoDB connection")


def get_mongodb():
    return mongodb_db