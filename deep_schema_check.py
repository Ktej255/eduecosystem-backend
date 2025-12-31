"""
Deep Database Schema Check
Compare SQLAlchemy model with actual RDS table structure
"""
import psycopg2

DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

def check_schema():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    # Get all columns from users table
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    
    print("=== USERS TABLE SCHEMA IN RDS ===")
    print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10} {'Default':<30}")
    print("=" * 90)
    for col in columns:
        col_name = col[0] or ""
        col_type = col[1] or ""
        nullable = col[2] or ""
        default = str(col[3])[:28] if col[3] else ""
        print(f"{col_name:<30} {col_type:<20} {nullable:<10} {default:<30}")
    
    # Check for specific critical columns
    print("\n=== CRITICAL COLUMN CHECK ===")
    critical_columns = ['id', 'email', 'hashed_password', 'is_active', 'is_approved', 'token_version', 'role']
    column_names = [c[0] for c in columns]
    
    for col in critical_columns:
        if col in column_names:
            print(f"✅ {col} - EXISTS")
        else:
            print(f"❌ {col} - MISSING!")
    
    # Get sample user data for chitrakumawat33@gmail.com
    print("\n=== USER DATA CHECK ===")
    cursor.execute("""
        SELECT id, email, hashed_password, is_active, is_approved, role, token_version, full_name
        FROM users
        WHERE email = 'chitrakumawat33@gmail.com'
    """)
    
    user = cursor.fetchone()
    if user:
        print(f"ID: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Password Hash: {user[2][:50]}..." if user[2] else "Password Hash: NULL!")
        print(f"Is Active: {user[3]}")
        print(f"Is Approved: {user[4]}")
        print(f"Role: {user[5]}")
        print(f"Token Version: {user[6]}")
        print(f"Full Name: {user[7]}")
        
        # Additional checks
        if not user[3]:
            print("\n⚠️ WARNING: User is NOT active!")
        if not user[4]:
            print("\n⚠️ WARNING: User is NOT approved!")
        if not user[2]:
            print("\n⚠️ CRITICAL: No password hash!")
    else:
        print("❌ USER NOT FOUND!")
        
        # List all users
        cursor.execute("SELECT id, email, is_active, is_approved FROM users ORDER BY id")
        users = cursor.fetchall()
        print(f"\nTotal users in database: {len(users)}")
        for u in users:
            print(f"  {u[0]}: {u[1]} | Active: {u[2]} | Approved: {u[3]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_schema()
