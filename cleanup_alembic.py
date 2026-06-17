#!/usr/bin/env python3
"""Clean up orphaned alembic revisions from the database."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

try:
    with engine.connect() as conn:
        # Drop the alembic_version table to reset migration tracking
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
        print("✓ Successfully dropped alembic_version table")
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    engine.dispose()
