from app.db.session import engine, Base
from app.models import *  # Import all models to ensure they are registered
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")


if __name__ == "__main__":
    init_db()
