from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

# Update admin password to "admin"
admin = db.query(User).filter(User.email == "admin@example.com").first()
if admin:
    admin.hashed_password = get_password_hash("admin")
    db.commit()
    print("✓ Admin password updated to 'admin'")
else:
    print("✗ Admin user not found")

db.close()
