#!/usr/bin/env python3
"""Clean up all constraints and sequences from the database."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

try:
    with engine.connect() as conn:
        # Drop all tables
        conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_catalog.pg_tables 
                          WHERE schemaname != 'pg_catalog' 
                          AND schemaname != 'information_schema')
                LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        
        # Drop all sequences
        conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT sequencename FROM pg_catalog.pg_sequences 
                          WHERE schemaname != 'pg_catalog' 
                          AND schemaname != 'information_schema')
                LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequencename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        
        conn.commit()
        print("✓ Successfully cleaned up all tables and sequences")
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    engine.dispose()
