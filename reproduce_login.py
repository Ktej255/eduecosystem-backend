
from app.db.session import SessionLocal




def test_login_flow():
    try:
        import sys
        import os
        os.environ["TESTING"] = "true" # Skip lifespan to prevent startup hang
        sys.stdout.reconfigure(encoding='utf-8')
        print("Starting login reproduction...")
        
        from fastapi.testclient import TestClient
        from app.core.config import settings
        from app import models, crud, schemas
        from app.core.security import get_password_hash
        from main import app
        from app.db.session import SessionLocal

        db = SessionLocal()
        email = "debug_login@example.com"
        password = "password123"
        
        # Clean up
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # Create user
        user_in = models.User(
            email=email,
            full_name="Debug User",
            hashed_password=get_password_hash(password),
            is_active=True,
            role="student"
        )
        db.add(user_in)
        db.commit()
        db.refresh(user_in)
        print(f"User created: {user_in.email}, Active: {user_in.is_active}, ID: {user_in.id}")
        db.close() # Close session to release locks

        client = TestClient(app)
        
        # Attempt login
        print(f"Attempting login with {email} / {password}")
        login_data = {
            "username": email,
            "password": password
        }
        
        resp = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
        print(f"Response Status: {resp.status_code}")
        print(f"Response Content: {resp.text}")
        
        if resp.status_code == 200:
            print("Login SUCCESS!")
        else:
            print("Login FAILED!")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")


if __name__ == "__main__":
    test_login_flow()
