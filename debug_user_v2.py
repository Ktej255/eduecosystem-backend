import sys
import os

# Append 'backend' to sys.path so 'app' is found as a top-level module
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.base import Base  # Triggers all model imports
from app.db.session import SessionLocal
from app.models.user import User

def debug_users():
    db = SessionLocal()
    try:
        # Check specific user
        target_email = "chitrakumawat33@gmail.com"
        user = db.query(User).filter(User.email == target_email).first()
        
        print(f"\n--- DEBUG: {target_email} ---")
        if user:
            print(f"  ID: {user.id}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Is Approved: {user.is_approved}")
            print(f"  Hashed Password: {user.hashed_password[:15]}..." if user.hashed_password else "  Hashed Password: NONE")
            print(f"  2FA Enabled: {user.is_2fa_enabled}")
            print(f"  Token Version: {user.token_version}")
        else:
            print("  STATUS: NOT FOUND IN DB")

        # List potential batch of legacy users
        print("\n--- Recent 20 Users ---")
        users = db.query(User).order_by(User.id.desc()).limit(20).all()
        for u in users:
            print(f"ID: {u.id} | {u.email} | Act:{u.is_active} | Appr:{u.is_approved}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_users()
