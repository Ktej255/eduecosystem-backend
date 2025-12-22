"""
Script to create or verify admin user for UPSC platform testing
"""
import sys
sys.path.append('.')

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_or_update_admin():
    db = SessionLocal()
    
    email = "ktej255@gmail.com"
    password = "Tej@1106"
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        print(f"✓ User exists: {user.email}")
        print(f"  - ID: {user.id}")
        print(f"  - Is Active: {user.is_active}")
        print(f"  - Is Superuser: {user.is_superuser}")
        
        # Update password and ensure superuser status
        user.hashed_password = get_password_hash(password)
        user.is_superuser = True
        user.is_active = True
        db.commit()
        print(f"✓ Updated user credentials and set as superuser")
    else:
        print(f"✗ User not found. Creating new admin user...")
        
        new_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✓ Created admin user: {new_user.email} (ID: {new_user.id})")
    
    db.close()
    print("\n✅ Admin user ready for login!")

if __name__ == "__main__":
    create_or_update_admin()
