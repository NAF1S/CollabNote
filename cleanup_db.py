#!/usr/bin/env python3
"""Clean up the database and reset alembic."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

try:
    with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nExisting tables: {tables}\n")
        
        # Drop the users table if it exists
        if 'users' in tables:
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            print("✓ Dropped 'users' table")
        
        # Drop the old User_creadintials table if it exists
        if 'User_creadintials' in tables:
            conn.execute(text("DROP TABLE IF EXISTS User_creadintials CASCADE"))
            print("✓ Dropped 'User_creadintials' table")
        
        # Drop the alembic_version table to reset migration tracking
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        print("✓ Dropped 'alembic_version' table")
        
        conn.commit()
        print("\n✓ Database cleanup complete")
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    engine.dispose()
