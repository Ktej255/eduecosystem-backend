import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.models.ras_planner import RASTopicProgress
from app.db.session import Base

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"
TARGET_EMAIL = "chitrakumawat33@gmail.com"

def fix_and_seed():
    engine = create_engine(PROD_DB_URL)
    
    print("Connecting to PROD RDS to fix ras_topic_progress table...")
    try:
        # 1. Drop existing table
        with engine.connect() as conn:
            print("Dropping old table...")
            conn.execute(text("DROP TABLE IF EXISTS ras_topic_progress CASCADE"))
            conn.commit()
            print("[OK] Dropped old ras_topic_progress")

        # 2. Recreate using SQLAlchemy model
        print("Recreating table from SQLAlchemy model...")
        RASTopicProgress.__table__.create(engine)
        print("[OK] Recreated ras_topic_progress with modern schema")

        # 3. Find User ID
        with engine.connect() as conn:
            row = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": TARGET_EMAIL}).fetchone()
            if not row:
                print(f"Error: User {TARGET_EMAIL} not found.")
                return
            user_id = row[0]
            print(f"Found user {TARGET_EMAIL} with ID: {user_id}")

            # 4. Seed 3 days of progress (rg_01 to rg_06)
            topics = ["rg_01", "rg_02", "rg_03", "rg_04", "rg_05", "rg_06"]
            now = datetime.now(timezone.utc)
            
            print(f"Seeding {len(topics)} topics as completed...")
            for topic_id in topics:
                conn.execute(text("""
                    INSERT INTO ras_topic_progress (user_id, topic_id, completed, hours_spent, completed_at, last_updated, mastery_level)
                    VALUES (:uid, :tid, TRUE, 1.5, :now, :now, 85)
                """), {"uid": user_id, "tid": topic_id, "now": now})
            
            conn.commit()
            print(f"[OK] Successfully seeded progress for {TARGET_EMAIL}")

            # 5. Verify count
            count = conn.execute(text("SELECT count(*) FROM ras_topic_progress WHERE user_id = :uid"), {"uid": user_id}).scalar()
            print(f"Verification: {count} entries exist in PROD for this user.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_and_seed()
