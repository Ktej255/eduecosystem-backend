"""
Script to check and fix production database schema.
"""
import os

# Set the DATABASE_URL to production
DATABASE_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

from sqlalchemy import create_engine, text

def check_database():
    """Check what tables exist in the database."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # List all tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"Found {len(tables)} tables:")
        for t in tables:
            print(f"  - {t}")
        
        # Check if users table exists
        if 'users' in tables:
            print("\nUsers table exists. Checking columns...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            print(f"Users table has {len(columns)} columns:")
            for c in columns:
                print(f"  - {c}")
        else:
            print("\nUsers table does NOT exist! Database needs to be initialized.")

if __name__ == "__main__":
    check_database()
