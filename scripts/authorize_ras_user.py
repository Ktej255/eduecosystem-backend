import os
import sys
from sqlalchemy import create_engine, text
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"
TARGET_EMAIL = "chitrakumawat33@gmail.com"

def authorize_user():
    engine = create_engine(PROD_DB_URL)
    
    print(f"Authorizing user {TARGET_EMAIL} for RAS in PROD RDS...")
    try:
        with engine.connect() as conn:
            # 1. Check if user exists
            result = conn.execute(text("SELECT id, email, is_ras_authorized, is_batch1_authorized, is_batch2_authorized FROM users WHERE email = :email"), {"email": TARGET_EMAIL}).fetchone()
            
            if not result:
                print(f"Error: User {TARGET_EMAIL} NOT FOUND in PROD database.")
                return
            
            user_id, email, ras, b1, b2 = result
            print(f"Found user: ID={user_id}, Current Flags: RAS={ras}, B1={b1}, B2={b2}")
            
            # 2. Update flags: Set RAS=True, Others=False (as per user request: "rest of any other thing not need to make only this knee you need to make it live")
            conn.execute(text("""
                UPDATE users 
                SET is_ras_authorized = TRUE, 
                    is_batch1_authorized = FALSE, 
                    is_batch2_authorized = FALSE 
                WHERE email = :email
            """), {"email": TARGET_EMAIL})
            
            conn.commit()
            print(f"[OK] User {TARGET_EMAIL} successfully authorized for RAS (and denied for others).")
            
            # 3. Verify
            new_result = conn.execute(text("SELECT is_ras_authorized, is_batch1_authorized, is_batch2_authorized FROM users WHERE email = :email"), {"email": TARGET_EMAIL}).fetchone()
            print(f"New Flags: RAS={new_result[0]}, B1={new_result[1]}, B2={new_result[2]}")
            
    except Exception as e:
        print(f"Error during authorization: {e}")

if __name__ == "__main__":
    authorize_user()
