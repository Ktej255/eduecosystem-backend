import sqlite3
import os

def list_tables(db_path):
    if not os.path.exists(db_path):
        print(f"\nDatabase {db_path} not found.")
        return

    print(f"\n--- Inspecting {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"{'Table Name':<30} | {'Row Count':<10}")
        print("-" * 45)
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"{table_name:<30} | {count:<10}")
            except:
                print(f"{table_name:<30} | ERROR")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for db in ["temp_inspect.db", "temp_inspect_v2.db", "app.db", "eduecosystem_upsc.db"]:
        list_tables(db)
