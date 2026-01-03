import sqlite3
import os

db_path = 'eduecosystem_v2.db'

# Delete the old database
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed {db_path}")

# Create fresh db with alembic_version set to the base revision
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE alembic_version(version_num VARCHAR(32) NOT NULL)")
conn.execute("INSERT INTO alembic_version VALUES ('9216918ff6cf')")
conn.commit()
conn.close()
print("Reset DB with alembic_version set to 9216918ff6cf")
