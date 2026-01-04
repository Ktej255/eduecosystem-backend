import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

from app.models.user import User

PROD_DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def inspect_prod():
    print(f"Connecting directly to PROD RDS...")
    try:
        engine = create_engine(PROD_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        user = db.query(User).filter(User.email == "chitrakumawat33@gmail.com").first()
        if user:
            print(f"User {user.email} found in PROD. ID={user.id}")
            if "ras_topic_progress" in tables:
                columns = [col['name'] for col in inspector.get_columns('ras_topic_progress')]
                print(f"Columns in 'ras_topic_progress': {columns}")
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT * FROM ras_topic_progress WHERE user_id = :uid"), {"uid": user.id}).fetchall()
                    print(f"RAS Progress entries for {user.email}: {len(result)}")
                    for p in result:
                        print(f"  - Entry: {p}")
            else:
                print("'ras_topic_progress' table NOT FOUND in PROD.")
        else:
            print(f"User chitrakumawat33@gmail.com NOT FOUND in PROD.")
            
        if "ras_topic_progress" in tables:
            with engine.connect() as conn:
                count = conn.execute(text("SELECT count(*) FROM ras_topic_progress")).scalar()
                print(f"Total rows in 'ras_topic_progress': {count}")
                if count > 0:
                    sample = conn.execute(text("SELECT * FROM ras_topic_progress LIMIT 5")).fetchall()
                    print(f"Sample data: {sample}")
        else:
            print("'ras_topic_progress' table NOT FOUND in PROD.")
            
        db.close()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_prod()
