"""
Comprehensive script to add ALL missing columns to SQLite database.
"""
import sqlite3
import os

db_path = "eduecosystem.db"
print(f"Using database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# All columns from User model that might be missing
columns_to_add = [
    ("users", "token_version", "INTEGER DEFAULT 1"),
    ("users", "totp_secret", "TEXT"),
    ("users", "revision_level", "TEXT"),
    ("users", "revision_exam_id", "TEXT"),
    ("users", "push_subscription", "TEXT"),
    ("users", "is_approved", "INTEGER DEFAULT 1"),
    ("users", "graphotherapy_enrollment_date", "DATETIME"),
    ("users", "is_graphotherapy_exclusive", "INTEGER DEFAULT 0"),
    ("users", "organization_id", "INTEGER"),
    ("users", "is_sso_user", "INTEGER DEFAULT 0"),
    ("users", "sso_external_id", "TEXT"),
    ("users", "is_verified", "INTEGER DEFAULT 0"),
    ("users", "is_ras_authorized", "INTEGER DEFAULT 0"),
    ("users", "is_batch1_authorized", "INTEGER DEFAULT 0"),
    ("users", "is_batch2_authorized", "INTEGER DEFAULT 0"),
    ("users", "created_at", "DATETIME"),
]

for table, column, col_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"✓ Added {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"  {column} already exists")
        else:
            print(f"  Error: {e}")

conn.commit()
conn.close()
print("\nDone!")
