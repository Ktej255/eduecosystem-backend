"""Check user record in database."""
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
    cur.execute("SELECT id, email, full_name, role, is_active, is_superuser, hashed_password FROM users WHERE email = %s", 
                ("chitrakumawat33@gmail.com",))
    user = cur.fetchone()
    
    if user:
        print(f"ID: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Name: {user[2]}")
        print(f"Role: {user[3]}")
        print(f"Is Active: {user[4]}")
        print(f"Is Superuser: {user[5]}")
        print(f"Password Hash: {user[6][:50]}...")
    else:
        print("User not found!")
        
finally:
    cur.close()
    conn.close()
