"""
Fix the admin password hash and verify it works.
"""
DATABASE_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

from sqlalchemy import create_engine, text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def fix_admin_password():
    """Update admin password with a fresh hash."""
    engine = create_engine(DATABASE_URL)
    
    # Generate fresh hash
    new_password = "Tej@1106"
    new_hash = pwd_context.hash(new_password)
    
    print(f"New password: {new_password}")
    print(f"New hash: {new_hash}")
    print(f"Hash length: {len(new_hash)}")
    
    with engine.connect() as conn:
        # First check current hash
        result = conn.execute(text("SELECT id, email, hashed_password FROM users WHERE email = 'ktej255@gmail.com'"))
        row = result.fetchone()
        if row:
            print(f"\nCurrent user: id={row[0]}, email={row[1]}")
            print(f"Current hash: {row[2]}")
            print(f"Current hash length: {len(row[2]) if row[2] else 0}")
            
            # Verify current hash
            if row[2]:
                try:
                    verified = pwd_context.verify(new_password, row[2])
                    print(f"Current hash verify result: {verified}")
                except Exception as e:
                    print(f"Current hash verify error: {e}")
        else:
            print("Admin user not found!")
            return
        
        # Update with new hash
        print("\nUpdating password...")
        conn.execute(text("UPDATE users SET hashed_password = :hash WHERE email = 'ktej255@gmail.com'"), {"hash": new_hash})
        conn.commit()
        print("Password updated!")
        
        # Verify new hash works
        result = conn.execute(text("SELECT hashed_password FROM users WHERE email = 'ktej255@gmail.com'"))
        new_stored_hash = result.fetchone()[0]
        verified = pwd_context.verify(new_password, new_stored_hash)
        print(f"New hash verify result: {verified}")

if __name__ == "__main__":
    fix_admin_password()
