import sys
import os
import time
from sqlalchemy import create_engine, text, inspect

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import Base

# Use a specific test DB file
db_file = f"test_debug_schema_{int(time.time())}.db"
url = f"sqlite:///./{db_file}"

print(f"Creating DB at {url}")
engine = create_engine(url)

print("Creating tables...")
Base.metadata.create_all(bind=engine)

print("Checking users table columns...")
inspector = inspect(engine)
columns = [c["name"] for c in inspector.get_columns("users")]
print(f"Columns: {columns}")

if "is_verified" in columns:
    print("SUCCESS: is_verified column exists!")
else:
    print("FAILURE: is_verified column MISSING!")

    print("Attempting manual fix...")
    with engine.connect() as conn:
        try:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")
            )
            conn.commit()
            print("Manual fix executed.")
        except Exception as e:
            print(f"Manual fix failed: {e}")

    # Check again
    columns_after = [c["name"] for c in inspector.get_columns("users")]
    if "is_verified" in columns_after:
        print("SUCCESS: Manual fix worked!")
    else:
        print("FAILURE: Manual fix did NOT work!")

# Clean up
if os.path.exists(db_file):
    try:
        os.remove(db_file)
        print("DB file removed.")
    except:
        pass
