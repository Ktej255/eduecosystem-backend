import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from app.db.session import Base

# Import all models


def test_models():
    print("Initializing engine...")
    engine = create_engine("sqlite:///:memory:")
    print("Creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_models()
