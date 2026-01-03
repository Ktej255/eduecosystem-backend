import sqlite3
import os

databases = [
    'eduecosystem_v2.db',
    'backend/eduecosystem_v2.db',
    'app.db',
    'backend/app.db',
    'eduecosystem.db',
    'backend/eduecosystem.db'
]

for db_path in databases:
    if not os.path.exists(db_path):
        continue
        
    print(f"\n--- Checking {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print("Tables count:", len(tables))
        print("Important tables:", [t for t in tables if t in ['users', 'study_sessions', 'alembic_version']])
        
        if 'users' in tables:
            cursor.execute("SELECT email FROM users LIMIT 1;")
            user = cursor.fetchone()
            print("Test User:", user[0] if user else "None")
            
        conn.close()
    except Exception as e:
        print(f"Error {db_path}: {e}")
