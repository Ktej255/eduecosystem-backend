import os
import sys
import getpass
from sqlalchemy import create_engine, text, inspect
import pandas as pd
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent dir to path to import app models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. AWS Source Configuration (From config.py logic)
AWS_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

# 2. Supabase Target Configuration
PROJECT_REF = "ffzikovynwnnlettdzgw"
logger.info("--- Eduecosystem Database Migration Tool ---")
logger.info("Target: Supabase Project " + PROJECT_REF)

# Get Password securely
db_password = os.getenv("DB_PASSWORD") or getpass.getpass("Enter your Supabase Database Password: ")
SUPABASE_DB_URL = f"postgresql://postgres:{db_password}@db.{PROJECT_REF}.supabase.co:5432/postgres"

def migrate():
    try:
        # Connect to Source and Target
        source_engine = create_engine(AWS_DB_URL)
        target_engine = create_engine(SUPABASE_DB_URL)
        
        logger.info("Testing connections...")
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ AWS Connected")
        
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Supabase Connected")

        # Step 1: Create Schema (Using SQL Alchemy Models)
        logger.info("Step 1: Creating Schema on Supabase...")
        from app.db.base import Base  # Import all models
        
        logger.info(f"DEBUG: Found tables in Meta: {list(Base.metadata.tables.keys())}")
        
        Base.metadata.create_all(bind=target_engine)
        logger.info("✅ Schema Created")

        # Step 2: Migrate Data
        logger.info("Step 2: Migrating Data...")
        
        inspector = inspect(source_engine)
        tables = inspector.get_table_names()
        
        # Disable FK checks on Target for bulk load
        with target_engine.connect() as target_conn:
            target_conn.execute(text("SET session_replication_role = 'replica';"))
            target_conn.commit()
            
            for table in tables:
                logger.info(f"  -> Migrating table: {table}")
                try:
                    # Read from Source
                    df = pd.read_sql_table(table, source_engine)
                    if df.empty:
                        logger.info(f"     (Skipping empty table)")
                        continue
                        
                    # Write to Target (Append mode, since schema exists)
                    df.to_sql(table, target_conn, if_exists='append', index=False)
                    logger.info(f"     ✅ Copied {len(df)} rows")
                except Exception as e:
                    logger.error(f"     ❌ Failed to migrate {table}: {e}")

            # Re-enable FK checks
            target_conn.execute(text("SET session_replication_role = 'origin';"))
            target_conn.commit()
            
        logger.info("--- MIGRATION COMPLETE ---")
        logger.info("Please update backend/app/core/config.py with the new Supabase URL.")

    except Exception as e:
        logger.error(f"Migration Failed: {e}")

if __name__ == "__main__":
    migrate()
