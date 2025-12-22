"""
Direct database password update
Updates the password directly in the database
"""
import sys
from sqlalchemy import create_engine, text
from app.core.security import get_password_hash
from app.core.config import settings

# Get database URL
db_url = settings.DATABASE_URL
print(f"Database URL: {db_url}")

# Create engine
engine = create_engine(db_url)

# New password
email = "ktej255@gmail.com"
new_password = "Tej@1106"
hashed_password = get_password_hash(new_password)

print(f"Email: {email}")
print(f"New password: {new_password}")
print(f"Hashed password: {hashed_password[:50]}...")

# Update password
with engine.connect() as conn:
    # Check if user exists
    result = conn.execute(text("SELECT id, email, role, is_superuser FROM users WHERE email = :email"), {"email": email})
    user = result.fetchone()
    
    if user:
        print(f"\nFound user:")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Role: {user[2]}")
        print(f"  Superuser: {user[3]}")
        
        # Update password
        conn.execute(
            text("UPDATE users SET hashed_password = :password, is_active = 1, is_verified = 1 WHERE email = :email"),
            {"password": hashed_password, "email": email}
        )
        conn.commit()
        
        print(f"\n✅ Password updated successfully!")
        print(f"You can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {new_password}")
    else:
        print(f"\n❌ User not found: {email}")
        print("Creating new user...")
        
        conn.execute(
            text("""
                INSERT INTO users (email, username, hashed_password, full_name, role, is_superuser, is_active, is_verified, is_premium, coins, streak_days)
                VALUES (:email, :username, :password, :full_name, :role, :is_superuser, :is_active, :is_verified, :is_premium, :coins, :streak_days)
            """),
            {
                "email": email,
                "username": "admin",
                "password": hashed_password,
                "full_name": "Admin User",
                "role": "admin",
                "is_superuser": True,
                "is_active": True,
                "is_verified": True,
                "is_premium": True,
                "coins": 10000,
                "streak_days": 0
            }
        )
        conn.commit()
        print(f"✅ User created successfully!")
