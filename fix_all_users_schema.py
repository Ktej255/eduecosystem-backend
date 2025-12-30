"""Check and fix users table - ensure all required fields have values."""
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
    
    # Check table columns
    print("=== Checking table columns ===")
    cur.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name = 'users' AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} (default: {col[2]})")
    
    # Check for NULL token_version values
    print("\n=== Checking for NULL token_version ===")
    cur.execute("SELECT id, email, token_version FROM public.users WHERE token_version IS NULL")
    null_users = cur.fetchall()
    print(f"Users with NULL token_version: {len(null_users)}")
    for u in null_users:
        print(f"  ID {u[0]}: {u[1]}")
    
    # Fix NULL token_version - set to 0
    if null_users:
        print("\n=== Fixing NULL token_version (setting to 0) ===")
        cur.execute("UPDATE public.users SET token_version = 0 WHERE token_version IS NULL RETURNING id, email")
        fixed = cur.fetchall()
        conn.commit()
        print(f"Fixed {len(fixed)} users")
        for f in fixed:
            print(f"  ID {f[0]}: {f[1]}")
    
    # Check for NULL is_2fa_enabled
    print("\n=== Checking for NULL is_2fa_enabled ===")
    cur.execute("SELECT id, email, is_2fa_enabled FROM public.users WHERE is_2fa_enabled IS NULL")
    null_2fa = cur.fetchall()
    print(f"Users with NULL is_2fa_enabled: {len(null_2fa)}")
    
    if null_2fa:
        print("\n=== Fixing NULL is_2fa_enabled (setting to FALSE) ===")
        cur.execute("UPDATE public.users SET is_2fa_enabled = FALSE WHERE is_2fa_enabled IS NULL RETURNING id, email")
        fixed = cur.fetchall()
        conn.commit()
        print(f"Fixed {len(fixed)} users")
    
    print("\n=== DONE ===")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
