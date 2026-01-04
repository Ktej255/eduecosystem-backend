import os
import sys

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

from app.db.session import SessionLocal
from app.models.user import User

email = "hitvar040@gmail.com"

def verify_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User found: ID={user.id}, Email={user.email}, Full Name={user.full_name}")
        else:
            print(f"User with email {email} not found.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_user()
