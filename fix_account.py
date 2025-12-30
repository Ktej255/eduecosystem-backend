"""
Create user without specifying ID (let database auto-generate).
"""
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
    
    # Check if user exists
    cur.execute("SELECT id, email FROM users WHERE email = %s", ("chitrakumawat33@gmail.com",))
    existing = cur.fetchone()
    
    if existing:
        print(f"User already exists with id={existing[0]}")
        # Update password instead
        new_hash = pwd_context.hash("chitrakumawat@33")
        cur.execute("UPDATE users SET hashed_password = %s WHERE email = %s", 
                    (new_hash, "chitrakumawat33@gmail.com"))
        print("Password updated!")
    else:
        # Insert new user - let database auto-generate ID
        new_hash = pwd_context.hash("chitrakumawat@33")
        cur.execute(
            """INSERT INTO users (email, full_name, hashed_password, role, is_active, is_superuser)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            ("chitrakumawat33@gmail.com", "Chitra Kumawat", new_hash, "student", True, False)
        )
        new_id = cur.fetchone()[0]
        print(f"Created new user with id={new_id}")
    
    conn.commit()
    print("\n✅ SUCCESS! You can now login with:")
    print("   Email: chitrakumawat33@gmail.com")
    print("   Password: chitrakumawat@33")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
