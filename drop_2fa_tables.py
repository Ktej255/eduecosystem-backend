import sqlite3

# Connect to the database
conn = sqlite3.connect("d:/Graphology/Master Software/Eduecosystem/backend/app.db")
cursor = conn.cursor()

# Drop 2FA tables if they exist
tables_to_drop = ["two_factor_backup_codes", "two_factor_auth"]

for table in tables_to_drop:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Dropped {table}")
    except Exception as e:
        print(f"Could not drop {table}: {e}")

conn.commit()
conn.close()
print("\nCleanup complete!")
