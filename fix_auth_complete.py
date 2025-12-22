"""
Complete Authentication Fix Script
This script will:
1. Check database connection
2. List all users
3. Update admin password properly
4. Test authentication
"""
import sys
sys.path.insert(0, 'D:\\Graphology\\Master Software\\Eduecosystem\\backend')

from sqlalchemy import create_engine, text
from app.core.security import get_password_hash, verify_password
from app.core.config import settings

print("=" * 70)
print("AUTHENTICATION FIX SCRIPT")
print("=" * 70)

# Database connection
db_url = settings.DATABASE_URL
print(f"\n1. Database URL: {db_url}")

engine = create_engine(db_url)

# Admin credentials
ADMIN_EMAIL = "ktej255@gmail.com"
ADMIN_PASSWORD = "Tej@1106"

print(f"\n2. Target Admin Account:")
print(f"   Email: {ADMIN_EMAIL}")
print(f"   Password: {ADMIN_PASSWORD}")

# Hash the password
hashed_password = get_password_hash(ADMIN_PASSWORD)
print(f"\n3. Password hashed successfully")
print(f"   Hash (first 50 chars): {hashed_password[:50]}...")

# Test the hash
test_verify = verify_password(ADMIN_PASSWORD, hashed_password)
print(f"\n4. Password verification test: {'✅ PASSED' if test_verify else '❌ FAILED'}")

with engine.connect() as conn:
    print("\n5. Checking existing users...")
    
    # List all users
    result = conn.execute(text("SELECT id, email, role, is_active, is_verified, is_superuser FROM users"))
    users = result.fetchall()
    
    print(f"   Found {len(users)} users:")
    for user in users:
        print(f"   - ID: {user[0]}, Email: {user[1]}, Role: {user[2]}, Active: {user[3]}, Verified: {user[4]}, Superuser: {user[5]}")
    
    # Check if admin exists
    result = conn.execute(text("SELECT id, email, hashed_password FROM users WHERE email = :email"), {"email": ADMIN_EMAIL})
    admin = result.fetchone()
    
    if admin:
        print(f"\n6. Admin user found (ID: {admin[0]})")
        print(f"   Updating password...")
        
        # Update password and ensure account is active
        conn.execute(
            text("""
                UPDATE users 
                SET hashed_password = :password,
                    is_active = 1,
                    is_verified = 1,
                    is_superuser = 1,
                    role = 'admin'
                WHERE email = :email
            """),
            {"password": hashed_password, "email": ADMIN_EMAIL}
        )
        conn.commit()
        
        print(f"   ✅ Password updated successfully!")
        
        # Verify the update
        result = conn.execute(text("SELECT hashed_password FROM users WHERE email = :email"), {"email": ADMIN_EMAIL})
        updated_hash = result.fetchone()[0]
        
        # Test if the stored hash works
        test_stored = verify_password(ADMIN_PASSWORD, updated_hash)
        print(f"\n7. Verification test with stored hash: {'✅ PASSED' if test_stored else '❌ FAILED'}")
        
    else:
        print(f"\n6. Admin user NOT found. Creating new admin...")
        
        # Create new admin user
        conn.execute(
            text("""
                INSERT INTO users (
                    email, username, hashed_password, full_name, role,
                    is_superuser, is_active, is_verified, is_premium,
                    coins, streak_days
                )
                VALUES (
                    :email, :username, :password, :full_name, :role,
                    :is_superuser, :is_active, :is_verified, :is_premium,
                    :coins, :streak_days
                )
            """),
            {
                "email": ADMIN_EMAIL,
                "username": "admin",
                "password": hashed_password,
                "full_name": "Admin User",
                "role": "admin",
                "is_superuser": 1,
                "is_active": 1,
                "is_verified": 1,
                "is_premium": 1,
                "coins": 10000,
                "streak_days": 0
            }
        )
        conn.commit()
        print(f"   ✅ Admin user created successfully!")

print("\n" + "=" * 70)
print("✅ AUTHENTICATION FIX COMPLETE!")
print("=" * 70)
print(f"\nYou can now login with:")
print(f"  Email: {ADMIN_EMAIL}")
print(f"  Password: {ADMIN_PASSWORD}")
print("\nThe password has been properly hashed and stored in the database.")
print("=" * 70)
