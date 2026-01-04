import os
import sys

# Add the backend directory to sys.path
backend_dir = r"d:\Graphology\Master Software\Eduecosystem\backend"
sys.path.append(backend_dir)

from app.db.session import engine, settings
from sqlalchemy import inspect

def inspect_db():
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"DATABASE_URL (host): {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {tables}")
        
        if "users" in tables:
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            from app.models.user import User
            count = db.query(User).count()
            print(f"User count in 'users' table: {count}")
            if count > 0:
                user = db.query(User).filter(User.email == "hitvar040@gmail.com").first()
                if user:
                    print(f"User hitvar040@gmail.com FOUND! ID={user.id}")
                else:
                    print(f"User hitvar040@gmail.com NOT FOUND among {count} users.")
                    # Let's see some sample emails
                    samples = db.query(User.email).limit(5).all()
                    print(f"Sample emails: {[s[0] for s in samples]}")
            db.close()
        else:
            print("'users' table NOT FOUND in this database.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
