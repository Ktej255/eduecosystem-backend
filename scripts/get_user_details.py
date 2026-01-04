import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def get_user_details():
    print(f"Getting full details for hitvar040@gmail.com...")
    try:
        engine = create_engine(PROD_DB_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users WHERE email = 'hitvar040@gmail.com'"))
            user = result.fetchone()
            if user:
                # Use result.keys() to get column names (SQLAlchemy 1.4/2.0)
                # For fetchone() result, it might depend on version.
                # In 1.4+, connection.execute(text(...)) returns a Result object.
                # The user object is a Row object.
                columns = result.keys()
                for col, val in zip(columns, user):
                    print(f"{col}: {val}")
            else:
                print(f"User not found.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_user_details()
