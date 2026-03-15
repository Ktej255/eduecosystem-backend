"""
Fix local SQLite database schema and seed test users.
Adds missing columns and creates test accounts for TestSprite testing.
"""
import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eduecosystem_v2.db")

def hash_password(password):
    """Simple bcrypt-compatible hash using passlib if available, else plain hash."""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    except ImportError:
        # Fallback - won't work with FastAPI auth but lets us proceed
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def main():
    print(f"Connecting to: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"Existing columns: {sorted(existing_columns)}")
    
    # All columns that might be missing
    columns_to_add = {
        "xp": "INTEGER DEFAULT 0",
        "streak_days": "INTEGER DEFAULT 0",
        "coins": "INTEGER DEFAULT 0",
        "token_version": "INTEGER DEFAULT 1",
        "is_approved": "BOOLEAN DEFAULT 1",
        "is_banned": "BOOLEAN DEFAULT 0",
        "email_notifications": "BOOLEAN DEFAULT 1",
        "is_premium": "BOOLEAN DEFAULT 0",
        "cashfree_customer_id": "VARCHAR NULL",
        "subscription_status": "VARCHAR DEFAULT 'free'",
        "graphotherapy_enrollment_date": "TIMESTAMP NULL",
        "is_graphotherapy_exclusive": "BOOLEAN DEFAULT 0",
        "organization_id": "INTEGER NULL",
        "is_sso_user": "BOOLEAN DEFAULT 0",
        "sso_external_id": "VARCHAR NULL",
        "is_verified": "BOOLEAN DEFAULT 0",
        "is_ras_authorized": "BOOLEAN DEFAULT 0",
        "is_batch1_authorized": "BOOLEAN DEFAULT 0",
        "is_batch2_authorized": "BOOLEAN DEFAULT 0",
        "totp_secret": "VARCHAR NULL",
        "revision_level": "VARCHAR NULL",
        "revision_exam_id": "VARCHAR NULL",
        "push_subscription": "JSON NULL",
        "last_login": "TIMESTAMP NULL",
        "role": "VARCHAR DEFAULT 'student'",
        "group_id": "INTEGER NULL",
        "username": "VARCHAR NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "purchased_subjects": "JSON DEFAULT '[]'",
    }
    
    added = 0
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name}")
                added += 1
            except Exception as e:
                print(f"  Skipped {col_name}: {e}")
    
    conn.commit()
    print(f"\nAdded {added} missing columns.")
    
    # Now seed test users
    print("\nSeeding test users...")
    
    hashed_student = hash_password("student123")
    hashed_admin = hash_password("admin123")
    
    users = [
        ("student@example.com", hashed_student, "Test Student", "student", 0, 1),
        ("admin@example.com", hashed_admin, "Test Admin", "admin", 1, 1),
    ]
    
    for email, pwd, name, role, is_super, is_active in users:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"  User already exists: {email}")
            continue
        
        try:
            cursor.execute(
                """INSERT INTO users (email, hashed_password, full_name, role, is_superuser, is_active, 
                   is_approved, is_verified, xp, coins, streak_days, token_version)
                   VALUES (?, ?, ?, ?, ?, ?, 1, 1, 0, 0, 0, 1)""",
                (email, pwd, name, role, is_super, is_active)
            )
            print(f"  Created user: {email} (role: {role})")
        except Exception as e:
            print(f"  Error creating {email}: {e}")
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT email, role, is_active FROM users")
    rows = cursor.fetchall()
    print(f"\nAll users in DB ({len(rows)}):")
    for row in rows:
        print(f"  {row[0]} | role={row[1]} | active={row[2]}")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
