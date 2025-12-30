"""Verify password and test login."""
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
    cur.execute("SELECT id, email, hashed_password, role, is_active FROM users WHERE email = %s", 
                ("chitrakumawat33@gmail.com",))
    user = cur.fetchone()
    
    if user:
        user_id, email, hashed_password, role, is_active = user
        print(f"User ID: {user_id}")
        print(f"Email: {email}")
        print(f"Role: {role}")
        print(f"Is Active: {is_active}")
        print(f"Hash: {hashed_password[:30]}...")
        
        # Verify password
        test_password = "chitrakumawat@33"
        if pwd_context.verify(test_password, hashed_password):
            print(f"\n✅ Password '{test_password}' is CORRECT!")
        else:
            print(f"\n❌ Password '{test_password}' is INCORRECT!")
            
            # Try to fix by updating
            new_hash = pwd_context.hash(test_password)
            cur.execute("UPDATE users SET hashed_password = %s, role = %s, is_active = %s WHERE id = %s",
                       (new_hash, 'student', True, user_id))
            conn.commit()
            print("Updated password, role and is_active!")
    else:
        print("User not found!")
        
finally:
    cur.close()
    conn.close()
