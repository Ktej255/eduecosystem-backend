import os
import sys
import getpass
from sqlalchemy import create_engine, text
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Supabase Configuration
PROJECT_REF = "ffzikovynwnnlettdzgw"
logger.info("--- Supabase Verification Tool ---")
logger.info(f"Target Project: {PROJECT_REF}")

# Get Password
db_password = os.getenv("DB_PASSWORD") or getpass.getpass("Enter your Supabase Database Password: ")
SUPABASE_DB_URL = f"postgresql://postgres:{db_password}@db.{PROJECT_REF}.supabase.co:5432/postgres"

def verify():
    try:
        engine = create_engine(SUPABASE_DB_URL)
        with engine.connect() as conn:
            logger.info("\n✅ Connected to Supabase successfully!")
            logger.info("Checking data counts...\n")

            # Check key tables
            tables_to_check = ["users", "courses", "enrollments", "student_stats"]
            
            total_records = 0
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT count(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"📊 Table '{table}': {count} records found.")
                    total_records += count
                except Exception:
                    logger.warning(f"⚠️ Table '{table}' not found or empty.")

            print("-" * 30)
            if total_records > 0:
                logger.info(f"🎉 SUCCESS: Found {total_records} total records across tables.")
                logger.info("The migration was successful.")
            else:
                logger.error("❌ ERROR: The database seems empty. Did the migration script finish?")

    except Exception as e:
        logger.error(f"\n❌ Connection Failed. Please check your password.\nError: {e}")

if __name__ == "__main__":
    verify()
