"""
Script to initialize the production database with all tables and create an admin user.
"""
import os
import sys

# Set environment to production before importing anything
os.environ["ENVIRONMENT"] = "production"
os.environ["DATABASE_URL"] = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"
os.environ["SECRET_KEY"] = "eduecosystem-super-secret-key-2025-production"

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.db.session import Base, engine

def init_database():
    """Create all tables in the database."""
    print("Creating all database tables...")
    
    # Import ALL models from the central models package
    # This ensures all models are registered with Base.metadata
    import app.models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")
    
    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nCreated {len(tables)} tables:")
    for t in sorted(tables):
        print(f"  - {t}")

def create_admin_user():
    """Create the admin user."""
    print("\nCreating admin user...")
    
    from app.db.session import SessionLocal
    from app.crud import user as crud_user
    from app.schemas.user import UserCreate
    
    db = SessionLocal()
    try:
        # Check if admin exists
        existing = crud_user.get_by_email(db, email="ktej255@gmail.com")
        if existing:
            print("Admin user already exists!")
            return
        
        # Create admin
        user_in = UserCreate(
            email="ktej255@gmail.com",
            password="Tej@1106",
            full_name="Master Admin",
            role="admin"
        )
        user = crud_user.create(db, obj_in=user_in)
        user.is_superuser = True
        user.is_active = True
        user.is_approved = True
        db.add(user)
        db.commit()
        print(f"Admin user created: {user.email}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    create_admin_user()
    print("\nDatabase initialization complete!")
