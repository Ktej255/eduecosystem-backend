import os
import sys
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def update_prod_db():
    engine = create_engine(PROD_DB_URL)
    
    print("Updating PROD RDS with missing columns...")
    try:
        with engine.connect() as conn:
            # 1. Add is_ras_authorized
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_ras_authorized BOOLEAN DEFAULT FALSE"))
                print("[OK] Added is_ras_authorized")
            except Exception as e:
                print(f"[INFO] is_ras_authorized exists or failed: {e}")
                
            # 2. Add is_batch1_authorized
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_batch1_authorized BOOLEAN DEFAULT FALSE"))
                print("[OK] Added is_batch1_authorized")
            except Exception as e:
                print(f"[INFO] is_batch1_authorized exists or failed: {e}")
                
            # 3. Add is_batch2_authorized
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_batch2_authorized BOOLEAN DEFAULT FALSE"))
                print("[OK] Added is_batch2_authorized")
            except Exception as e:
                print(f"[INFO] is_batch2_authorized exists or failed: {e}")
            
            # Commit the changes (Postgres usually handles this if not in transaction, but connect() might start one)
            conn.commit()
            
        print("\nStamping database with revision f73ef2a321c3...")
        os.environ["DATABASE_URL"] = PROD_DB_URL
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "f73ef2a321c3")
        print("[OK] Stamped with f73ef2a321c3")
        
    except Exception as e:
        print(f"Error updating PROD DB: {e}")

if __name__ == "__main__":
    update_prod_db()
