"""
Script to grant Batch #2 access to specific users.
Usage: python grant_batch2_access.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

# Target emails - Paid students who need Batch #2 access
TARGET_EMAILS = [
    "hitvar040@gmail.com",
    "itspanwar111@gmail.com"
]

def grant_batch2_access():
    engine = create_engine(PROD_DB_URL)
    
    print("=" * 60)
    print("Granting Batch #2 Access to Paid Students")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            for email in TARGET_EMAILS:
                print(f"\nProcessing: {email}")
                print("-" * 40)
                
                # 1. Check if user exists
                result = conn.execute(
                    text("SELECT id, email, is_ras_authorized, is_batch1_authorized, is_batch2_authorized FROM users WHERE email = :email"), 
                    {"email": email}
                ).fetchone()
                
                if not result:
                    print(f"  [ERROR] User {email} NOT FOUND in database.")
                    continue
                
                user_id, email_db, ras, b1, b2 = result
                print(f"  Found user: ID={user_id}")
                print(f"  Current Flags: RAS={ras}, Batch1={b1}, Batch2={b2}")
                
                # 2. Grant Batch #2 access (set is_batch2_authorized = True)
                conn.execute(text("""
                    UPDATE users 
                    SET is_batch2_authorized = TRUE
                    WHERE email = :email
                """), {"email": email})
                
                conn.commit()
                
                # 3. Verify the update
                new_result = conn.execute(
                    text("SELECT is_ras_authorized, is_batch1_authorized, is_batch2_authorized FROM users WHERE email = :email"), 
                    {"email": email}
                ).fetchone()
                print(f"  [SUCCESS] Updated Flags: RAS={new_result[0]}, Batch1={new_result[1]}, Batch2={new_result[2]}")
            
            print("\n" + "=" * 60)
            print("Batch #2 access grant completed!")
            print("=" * 60)
                
    except Exception as e:
        print(f"[ERROR] During authorization: {e}")

if __name__ == "__main__":
    grant_batch2_access()
