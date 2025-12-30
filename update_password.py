"""
Direct SQL script to update a user's password.
"""
import psycopg2
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Supabase connection
conn = psycopg2.connect(
    host="aws-1-ap-south-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.ffzikovynwnnlettdzgw",
    password="Edueco2025!Secure"
)

try:
    cur = conn.cursor()
    
    # Generate the new password hash
    new_hash = get_password_hash("chitrakumawat@33")
    print(f"New password hash: {new_hash[:20]}...")
    
    # Update the password
    cur.execute(
        "UPDATE users SET hashed_password = %s WHERE email = %s",
        (new_hash, "chitrakumawat33@gmail.com")
    )
    
    rows_affected = cur.rowcount
    conn.commit()
    
    if rows_affected > 0:
        print(f"Password updated successfully for chitrakumawat33@gmail.com")
    else:
        print("No user found with that email.")
        
finally:
    cur.close()
    conn.close()
