from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()

# Check admin user
admin = db.query(User).filter(User.email == "admin@example.com").first()
if admin:
    print("Admin user found:")
    print(f"  Email: {admin.email}")
    print(f"  Full Name: {admin.full_name}")
    print(f"  Role: {admin.role}")
    print(f"  Is Active: {admin.is_active}")
    print(f"  Hashed Password (first 20 chars): {admin.hashed_password[:20]}...")

    # Test password verification
    test_passwords = ["admin", "admin123", "password"]
    for pwd in test_passwords:
        if verify_password(pwd, admin.hashed_password):
            print(f"  ✓ Password '{pwd}' is CORRECT")
        else:
            print(f"  ✗ Password '{pwd}' is incorrect")
else:
    print("Admin user NOT found in database")

# List all users
print("\nAll users in database:")
users = db.query(User).all()
for user in users:
    print(
        f"  - {user.email} ({user.full_name}) - Role: {user.role if hasattr(user, 'role') else 'N/A'}"
    )
