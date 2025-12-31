from app.db.session import SessionLocal
from app.models.user import User

def check_user(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User Found: {user.email}")
            print(f"  ID: {user.id}")
            print(f"  Active: {user.is_active}")
            print(f"  Approved: {user.is_approved}")
            print(f"  Superuser: {user.is_superuser}")
            print(f"  2FA Enabled: {user.is_2fa_enabled}")
            print(f"  Token Version: {user.token_version}")
            print(f"  Password Hash: {user.hashed_password[:10]}..." if user.hashed_password else "  Password Hash: NONE")
        else:
            print(f"User {email} NOT FOUND in database.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user("chitrakumawat33@gmail.com")
