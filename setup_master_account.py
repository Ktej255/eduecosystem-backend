"""
Setup Master Teacher Account
Run this script to set ktej255@gmail.com as the master teacher/admin account
"""
import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
# Import base to register all models
import app.db.base
from app.models.user import User
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MASTER_EMAIL = "ktej255@gmail.com"
MASTER_PASSWORD = "Tej@1106"  # Updated password


async def setup_master_account():
    """Set up master teacher account with full permissions"""
    db = SessionLocal()
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == MASTER_EMAIL).first()
        
        if user:
            logger.info(f"User {MASTER_EMAIL} already exists. Updating permissions...")
            # Update existing user
            user.role = "admin"
            user.is_superuser = True
            user.is_active = True
            user.is_verified = True
            user.is_premium = True
            user.full_name = "Master Teacher"
        else:
            logger.info(f"Creating new master account for {MASTER_EMAIL}...")
            # Create new user
            user = User(
                email=MASTER_EMAIL,
                username="master_teacher",
                hashed_password=get_password_hash(MASTER_PASSWORD),
                full_name="Master Teacher",
                role="admin",
                is_superuser=True,
                is_active=True,
                is_verified=True,
                is_premium=True,
                coins=10000,
                streak_days=0
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        logger.info("=" * 60)
        logger.info("✅ Master Account Setup Complete!")
        logger.info("=" * 60)
        logger.info(f"Email: {MASTER_EMAIL}")
        logger.info(f"Password: {MASTER_PASSWORD}")
        logger.info(f"Role: {user.role}")
        logger.info(f"Superuser: {user.is_superuser}")
        logger.info(f"Premium: {user.is_premium}")
        logger.info(f"User ID: {user.id}")
        logger.info("=" * 60)
        logger.info("⚠️  IMPORTANT: Change the password after first login!")
        logger.info("=" * 60)
        
        return user
        
    except Exception as e:
        logger.error(f"Error setting up master account: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(setup_master_account())
