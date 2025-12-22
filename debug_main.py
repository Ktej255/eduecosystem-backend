import sys
import os

sys.path.append(os.getcwd())
from sqlalchemy import create_engine
from app.db.session import Base

engine = create_engine("sqlite:///./debug_test_main.db")
print("Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
