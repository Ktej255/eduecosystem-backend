
import sqlite3
import os

DB_PATH = "eduecosystem.db"

def patch_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "revision_level" not in columns:
            print("Adding revision_level column...")
            cursor.execute("ALTER TABLE users ADD COLUMN revision_level VARCHAR")
        else:
            print("revision_level column already exists.")

        if "revision_exam_id" not in columns:
            print("Adding revision_exam_id column...")
            cursor.execute("ALTER TABLE users ADD COLUMN revision_exam_id VARCHAR")
        else:
            print("revision_exam_id column already exists.")
            
        conn.commit()
        print("Database patch completed successfully.")
        
    except Exception as e:
        print(f"Error patching database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch_db()
