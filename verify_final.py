"""Final verification of user in database."""
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
    
    cur.execute("""
        SELECT id, email, full_name, role, is_active, is_approved, hashed_password 
        FROM public.users 
        WHERE email = %s
    """, (email,))
    
    user = cur.fetchone()
    if user:
        print(f"ID: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Name: {user[2]}")
        print(f"Role: {user[3]}")
        print(f"is_active: {user[4]}")
        print(f"is_approved: {user[5]}")
        print(f"Password hash exists: {bool(user[6])}")
        
        # Verify password
        is_valid = pwd_context.verify(password, user[6])
        print(f"Password '{password}' is valid: {is_valid}")
        
        if not is_valid:
            print("\nFIXING PASSWORD...")
            new_hash = pwd_context.hash(password)
            cur.execute("UPDATE public.users SET hashed_password = %s WHERE email = %s", (new_hash, email))
            conn.commit()
            print("Password fixed!")
    else:
        print("USER NOT FOUND!")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
