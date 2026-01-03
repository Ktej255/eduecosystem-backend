import sqlite3
conn = sqlite3.connect('eduecosystem_v2.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Total tables: {len(tables)}")
print(f"'users' exists: {'users' in tables}")
print(f"'study_sessions' exists: {'study_sessions' in tables}")
if 'users' in tables:
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"Users count: {cursor.fetchone()[0]}")
conn.close()
