"""Fix all users with NULL token_version and is_2fa_enabled."""
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
    
    # Update all users to have default values for required fields
    cur.execute("""
        UPDATE public.users 
        SET 
            token_version = COALESCE(token_version, 0),
            is_2fa_enabled = COALESCE(is_2fa_enabled, FALSE)
        RETURNING id, email, token_version, is_2fa_enabled
    """)
    
    updated = cur.fetchall()
    conn.commit()
    
    print(f"Updated {len(updated)} users:")
    for u in updated:
        print(f"  ID {u[0]}: {u[1]} - token_version={u[2]}, is_2fa_enabled={u[3]}")
    
    print("\nDONE - All users now have valid token_version and is_2fa_enabled values")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
