import sqlite3
import os

db_path = "eduecosystem.db"

def check_local_progress():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    target_email = "chitrakumawat33@gmail.com"
    
    print(f"Checking local progress for {target_email} in {db_path}...")
    
    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (target_email,))
        row = cursor.fetchone()
        if not row:
            print(f"User {target_email} not found in local DB.")
            return
            
        user_id = row[0]
        print(f"Found user locally with ID: {user_id}")
        
        # Check ras_topic_progress
        cursor.execute("SELECT * FROM ras_topic_progress WHERE user_id = ?", (user_id,))
        progress = cursor.fetchall()
        
        print(f"Found {len(progress)} progress entries for {target_email} in local SQLite.")
        for p in progress:
            print(f"  - Entry: {p}")
            
    except Exception as e:
        print(f"Error checking local DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_local_progress()
