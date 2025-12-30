"""Final fix - update user in public.users with all required fields."""
import psycopg2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = psycopg2.connect(
    host="aws-1-ap-south-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.ffzikovynwnnlettdzgw",
    password="Edueco2025!Secure"
)

try:
    cur = conn.cursor()
    
    # First check current state
    cur.execute("""
        SELECT id, email, full_name, role, is_active, is_superuser, token_version, hashed_password
        FROM public.users 
        WHERE email = %s
    """, ("chitrakumawat33@gmail.com",))
    
    user = cur.fetchone()
    if user:
        print("Current state:")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]}")
        print(f"  Role: {user[3]}")
        print(f"  Is Active: {user[4]}")
        print(f"  Is Superuser: {user[5]}")
        print(f"  Token Version: {user[6]}")
        print(f"  Has Password: {bool(user[7])}")
        
        # Update with correct password
        new_hash = pwd_context.hash("chitrakumawat@33")
        cur.execute("""
            UPDATE public.users SET 
                hashed_password = %s,
                is_active = TRUE,
                token_version = COALESCE(token_version, 0)
            WHERE email = %s
        """, (new_hash, "chitrakumawat33@gmail.com"))
        conn.commit()
        
        print("\n✅ Password updated!")
        print("   Email: chitrakumawat33@gmail.com")
        print("   Password: chitrakumawat@33")
        
        # Verify password
        if pwd_context.verify("chitrakumawat@33", new_hash):
            print("   Password verification: ✅ PASSED")
    else:
        print("❌ User not found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
