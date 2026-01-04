import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def find_user_raw():
    print(f"Searching for user in PROD via RAW SQL...")
    try:
        engine = create_engine(PROD_DB_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT id, email, full_name, hashed_password FROM users WHERE email = 'hitvar040@gmail.com'"))
            user = result.fetchone()
            if user:
                print(f"User FOUND! ID={user[0]}, Email={user[1]}, Full Name={user[2]}")
                print(f"Current Hashed Password: {user[3]}")
            else:
                print(f"User hitvar040@gmail.com NOT FOUND.")
                
                # Check for table structure
                result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
                columns = [row[0] for row in result.fetchall()]
                print(f"Columns in 'users' table: {columns}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_user_raw()
