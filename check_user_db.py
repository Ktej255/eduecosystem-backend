import asyncio
from app.db.session import SessionLocal
from app.models.user import User
from sqlalchemy import select

async def check_user():
    db = SessionLocal()
    try:
        # Check for Ktej255@gmail.com
        result = db.execute(select(User).where(User.email == "Ktej255@gmail.com"))
        user = result.scalar_one_or_none()
        if user:
            print(f"USER_FOUND: {user.email}")
            print(f"IS_ACTIVE: {user.is_active}")
            print(f"HAS_PASSWORD: {user.hashed_password is not None}")
        else:
            print("USER_NOT_FOUND")
            # List all users for debugging
            result = db.execute(select(User.email))
            emails = result.scalars().all()
            print(f"AVAILABLE_USERS: {emails}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_user())
