import os
import sys

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

from app.db.session import SessionLocal
from app.models.user import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Total users found: {len(users)}")
        for user in users:
            print(f"ID={user.id}, Email={user.email}, Role={user.role}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
