from app.db.session import SessionLocal
from app.crud import user
from app.schemas.user import UserCreate

def create_verification_user():
    db = SessionLocal()
    email = "verification_student@example.com"
    password = "verification_password"
    
    existing_user = user.get_by_email(db, email=email)
    if existing_user:
        print(f"User {email} already exists.")
        return

    try:
        user_in = UserCreate(
            email=email,
            password=password,
            full_name="Verification Student",
            is_active=True
        )
        user.create(db, obj_in=user_in)
        print(f"User {email} created successfully.")
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    create_verification_user()
