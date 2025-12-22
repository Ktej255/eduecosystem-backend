"""
Initialize database tables and create master admin user
"""
import sys
sys.path.append('.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def init_and_create_admin():
    print("Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    db = SessionLocal()
    
    email = "ktej255@gmail.com"
    password = "Tej@1106"
    
    try:
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
            user.role = "admin"
            db.commit()
            print(f"✓ Updated user credentials and set as superuser")
        else:
            print(f"✗ User not found. Creating new admin user...")
            
            new_user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="Master Admin",
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"✓ Created admin user: {new_user.email} (ID: {new_user.id})")
        
        print("\n✅ Admin user ready for login!")
        print(f"\n📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"🔗 Login URL: http://localhost:3000/login")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_and_create_admin()
