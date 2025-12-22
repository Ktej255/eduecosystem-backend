import sys
import os
from sqlalchemy.exc import IntegrityError

# Add backend directory to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def debug_create_user():
    db = SessionLocal()
    try:
        print("Attempting to create user...")
        user = User(
            email="debug_direct_insert@gmail.com",
            hashed_password=get_password_hash("password123"),
            full_name="Debug Direct Insert",
            role="student",
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        print("User created successfully!")
        db.refresh(user)
        print(f"User ID: {user.id}")
    except Exception as e:
        print(f"FAILED to create user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    debug_create_user()
