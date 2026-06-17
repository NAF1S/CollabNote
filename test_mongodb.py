#!/usr/bin/env python3
"""Test MongoDB connection."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_NAME = os.getenv("DATABASE_NAME", "mongodb")

async def test_connection():
    print(f"Attempting to connect to: {MONGODB_URL}")
    print(f"Database name: {MONGODB_NAME}")
    
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        
        # Test the connection by accessing server info
        await client.admin.command('ping')
        print("✓ Successfully connected to MongoDB")
        
        # Try to access the database
        db = client[MONGODB_NAME]
        print(f"✓ Accessed database: {MONGODB_NAME}")
        
        # Try to insert a test document
        result = await db.test_collection.insert_one({"test": "document"})
        print(f"✓ Successfully inserted test document: {result.inserted_id}")
        
        # Clean up
        await db.test_collection.delete_one({"test": "document"})
        print("✓ Test document cleaned up")
        
        client.close()
        print("✓ Connection closed successfully")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
