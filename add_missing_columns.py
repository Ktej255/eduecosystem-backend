"""Add missing columns to users table for authentication to work."""
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
    
    # First, check what columns exist
    print("=== Current columns in users table ===")
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'users' AND table_schema = 'public'
    """)
    existing_cols = [r[0] for r in cur.fetchall()]
    print(f"Existing columns: {existing_cols}")
    
    # Add is_2fa_enabled if missing
    if 'is_2fa_enabled' not in existing_cols:
        print("\nAdding is_2fa_enabled column...")
        cur.execute("ALTER TABLE public.users ADD COLUMN is_2fa_enabled BOOLEAN DEFAULT FALSE")
        print("Added is_2fa_enabled column with default FALSE")
    else:
        print("\nis_2fa_enabled column already exists")
    
    # Add token_version if missing
    if 'token_version' not in existing_cols:
        print("\nAdding token_version column...")
        cur.execute("ALTER TABLE public.users ADD COLUMN token_version INTEGER DEFAULT 0")
        print("Added token_version column with default 0")
    else:
        print("\ntoken_version column already exists")
    
    conn.commit()
    
    # Verify all users have values
    print("\n=== Verifying all users have values ===")
    cur.execute("SELECT id, email, is_2fa_enabled, token_version FROM public.users ORDER BY id")
    users = cur.fetchall()
    for u in users:
        print(f"  ID {u[0]}: {u[1]} | 2FA: {u[2]} | TokenVer: {u[3]}")
    
    print("\nDONE!")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
