import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

from app.core.security import get_password_hash

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def update_password():
    email = "hitvar040@gmail.com"
    new_password = "Mohit 4m"
    
    print(f"Generating hash for '{new_password}'...")
    hashed_password = get_password_hash(new_password)
    
    print(f"Updating user {email} in PROD...")
    try:
        engine = create_engine(PROD_DB_URL)
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                # Using Raw SQL to avoid model mismatch issues
                result = connection.execute(text("""
                    UPDATE users 
                    SET hashed_password = :hp, 
                        is_verified = :iv, 
                        is_approved = :ia, 
                        token_version = :tv
                    WHERE email = :email
                    RETURNING id
                """), {
                    "hp": hashed_password,
                    "iv": True,
                    "ia": True,
                    "tv": 1,
                    "email": email
                })
                updated_id = result.fetchone()
                if updated_id:
                    print(f"Successfully updated user ID {updated_id[0]}")
                    trans.commit()
                else:
                    print(f"User {email} not found during update.")
                    trans.rollback()
            except Exception as e:
                print(f"Error during update: {e}")
                trans.rollback()
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_password()
