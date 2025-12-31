
import os
import sys
from sqlalchemy import create_engine

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.db.session import Base
from app.models.ai_coaching import CoachingSession

def create_tables():
    print("--- Creating Coaching Tables ---")
    engine = create_engine(settings.DATABASE_URL)
    
    # Create tables defined in Base metadata (that are imported)
    # We only want to create the new one, but create_all skips existing ones usually
    print(f"Creating table: {CoachingSession.__tablename__}")
    Base.metadata.create_all(bind=engine)
    print("--- Done ---")

if __name__ == "__main__":
    create_tables()
