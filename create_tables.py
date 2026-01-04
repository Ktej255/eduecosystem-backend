
from app.db.session import engine
from app.db.base import Base
# Make sure to import all models so they are registered
from app.models.batch1 import Batch1Segment
from app.models.user import User

print("Creating all tables in SQLite DB...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully (if they didn't exist).")
except Exception as e:
    print(f"❌ Failed to create tables: {e}")
