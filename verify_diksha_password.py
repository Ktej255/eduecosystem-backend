"""Verify password against stored hash for dikshajakhar0212@gmail.com"""
import psycopg2
from passlib.context import CryptContext

# Password context (same as used in backend)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Connect to database
conn = psycopg2.connect(
    host="aws-1-ap-south-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.ffzikovynwnnlettdzgw",
    password="Edueco2025!Secure"
)

try:
    cur = conn.cursor()
    
    email = "dikshajakhar0212@gmail.com"
    password_to_check = "diksha@123"
    
    # Get the stored hash
    cur.execute("SELECT hashed_password FROM public.users WHERE email = %s", (email,))
    result = cur.fetchone()
    
    if result:
        stored_hash = result[0]
        print(f"Email: {email}")
        print(f"Password to check: {password_to_check}")
        print(f"Stored hash (first 30 chars): {stored_hash[:30]}...")
        
        # Verify the password
        is_valid = pwd_context.verify(password_to_check, stored_hash)
        print(f"\nPassword Match: {is_valid}")
        
        if is_valid:
            print("\n✅ PASSWORD IS CORRECT - Login should work!")
        else:
            print("\n❌ PASSWORD DOES NOT MATCH - Need to reset password")
    else:
        print(f"User {email} not found!")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
