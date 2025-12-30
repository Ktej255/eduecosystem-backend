"""Add missing columns to users table."""
import psycopg2

conn = psycopg2.connect(
    host="aws-1-ap-south-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.ffzikovynwnnlettdzgw",
    password="Edueco2025!Secure"
)

try:
    cur = conn.cursor()
    
    # Add missing columns
    columns_to_add = [
        ("is_2fa_enabled", "BOOLEAN DEFAULT FALSE"),
        ("token_version", "INTEGER DEFAULT 0"),
        ("is_approved", "BOOLEAN DEFAULT TRUE"),
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"✅ Added column: {col_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"⏩ Column {col_name} already exists")
            else:
                print(f"❌ Failed to add {col_name}: {e}")
    
    conn.commit()
    
    # Now update the user
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    new_hash = pwd_context.hash("chitrakumawat@33")
    
    cur.execute("""
        UPDATE users SET 
            hashed_password = %s,
            role = 'student',
            is_active = TRUE,
            is_superuser = FALSE,
            is_2fa_enabled = FALSE,
            token_version = 0,
            is_approved = TRUE
        WHERE email = %s
        RETURNING id, email
    """, (new_hash, "chitrakumawat33@gmail.com"))
    
    result = cur.fetchone()
    if result:
        print(f"\n✅ User updated: {result[1]} (ID: {result[0]})")
        print("   Password: chitrakumawat@33")
        print("   is_2fa_enabled: FALSE")
        print("   token_version: 0")
        conn.commit()
    else:
        print("❌ User not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()
