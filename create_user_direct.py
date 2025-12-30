"""Create user without specifying ID - let database auto-generate."""
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
    
    email = "chitrakumawat33@gmail.com"
    password = "chitrakumawat@33"
    full_name = "Chitra Kumawat"
    
    # Get max ID and reset sequence
    cur.execute("SELECT MAX(id) FROM public.users")
    max_id = cur.fetchone()[0] or 0
    print(f"Current max ID: {max_id}")
    
    # Reset the sequence to be after max ID
    cur.execute(f"SELECT setval('users_id_seq', {max_id + 1})")
    print(f"Sequence reset to: {max_id + 1}")
    
    # Create password hash
    password_hash = pwd_context.hash(password)
    
    # Insert without specifying ID
    cur.execute("""
        INSERT INTO public.users (email, full_name, hashed_password, role, is_active, is_superuser, token_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, email, role, is_active
    """, (email, full_name, password_hash, 'student', True, False, 0))
    
    result = cur.fetchone()
    if result:
        conn.commit()
        print(f"\n✅ USER CREATED SUCCESSFULLY!")
        print(f"   ID: {result[0]}")
        print(f"   Email: {result[1]}")
        print(f"   Role: {result[2]}")
        print(f"   Is Active: {result[3]}")
        print(f"\n   🔑 LOGIN CREDENTIALS:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()
