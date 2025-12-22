import sys
import os

# Add the backend directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from sqlalchemy.orm import Session

def create_user(db: Session, email: str, password: str, role: str, is_superuser: bool = False, full_name: str = None):
    user = crud_user.get_by_email(db, email=email)
    if user:
        print(f"ℹ️  User already exists: {email} (Role: {user.role})")
        return user
    
    user_in = UserCreate(
        email=email,
        password=password,
        role=role,
        full_name=full_name or role.capitalize(),
        is_superuser=is_superuser
    )
    user = crud_user.create(db, obj_in=user_in)
    print(f"✅ Created user: {email} (Role: {user.role})")
    return user

def main():
    print("🌱 Starting user seeder...\n")
    db = SessionLocal()
    try:
        # Create Student
        create_user(
            db, 
            email="student@example.com", 
            password="student123", 
            role="student", 
            full_name="Test Student"
        )

        # Create Admin
        create_user(
            db, 
            email="admin@example.com", 
            password="admin123", 
            role="admin", 
            is_superuser=True, 
            full_name="Test Admin"
        )
        
        print("\n✅ User seeding complete!")
        print("\n📝 Credentials:")
        print("   Student: student@example.com / student123")
        print("   Admin:   admin@example.com   / admin123")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
