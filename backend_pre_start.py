import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.core.security import get_password_hash
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Safely create master admin user without duplicate key errors
    try:
        master_email = settings.FIRST_SUPERUSER
        master_pass = settings.FIRST_SUPERUSER_PASSWORD

        user = db.query(User).filter(User.email == master_email).first()
        if not user:
            logger.info(f"Creating initial superuser: {master_email}")
            user = User(
                email=master_email,
                hashed_password=get_password_hash(master_pass),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Superuser created successfully.")
        else:
            logger.info(f"Superuser {master_email} already exists. Ensuring admin role is set.")
            if not user.is_superuser or user.role != "admin":
                user.is_superuser = True
                user.role = "admin"
                # Optionally reset password to env if we need forced sync, but safer not to in prod
                db.commit()
                logger.info("Superuser role verified/updated.")

    except Exception as e:
        logger.error(f"Error during initial data script: {e}")
        db.rollback()
        raise

def main() -> None:
    logger.info("Initializing service...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Service initialized.")

if __name__ == "__main__":
    main()
