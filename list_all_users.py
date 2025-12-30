"""Get complete list of all registered users in the database."""
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
    
    # Get all users from public.users table
    print("=" * 80)
    print("ALL REGISTERED USERS IN public.users TABLE")
    print("=" * 80)
    cur.execute("""
        SELECT id, email, full_name, role, is_active, is_approved, hashed_password IS NOT NULL as has_password
        FROM public.users 
        ORDER BY id
    """)
    
    users = cur.fetchall()
    print(f"\nTotal: {len(users)} users\n")
    
    for user in users:
        print(f"ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]}")
        print(f"  Role: {user[3]}")
        print(f"  Active: {user[4]}")
        print(f"  Approved: {user[5]}")
        print(f"  Has Password: {user[6]}")
        print()
    
    # Check if specific email exists
    target_email = "dikshajakhar0212@gmail.com"
    print("=" * 80)
    print(f"CHECKING FOR: {target_email}")
    print("=" * 80)
    
    cur.execute("SELECT * FROM public.users WHERE LOWER(email) = LOWER(%s)", (target_email,))
    result = cur.fetchone()
    
    if result:
        print(f"FOUND: User exists in database")
        print(f"Details: {result}")
    else:
        print(f"NOT FOUND: {target_email} does NOT exist in public.users table!")
    
    # Also check auth.users table (Supabase auth)
    print("\n" + "=" * 80)
    print("CHECKING auth.users TABLE (Supabase Auth)")
    print("=" * 80)
    
    cur.execute("SELECT id, email FROM auth.users ORDER BY created_at")
    auth_users = cur.fetchall()
    print(f"Total in auth.users: {len(auth_users)}\n")
    for au in auth_users:
        print(f"  {au[0][:8]}... | {au[1]}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
