from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User

db = SessionLocal()

user_in = {
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "is_active": True,
}

user = db.query(User).filter(User.email == user_in["email"]).first()
if not user:
    user = User(
        email=user_in["email"],
        hashed_password=get_password_hash(user_in["password"]),
        full_name=user_in["full_name"],
        is_active=user_in["is_active"],
    )
    db.add(user)
    db.commit()
    print("Test User created successfully.")
else:
    print("Test User already exists.")
