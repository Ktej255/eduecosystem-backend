"""Check auth.users table (Supabase's built-in auth table)."""
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
    
    # Check auth schema tables
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'auth'
    """)
    print("Tables in 'auth' schema:")
    for t in cur.fetchall():
        print(f"  {t[0]}.{t[1]}")
    
    # Try to query auth.users directly
    email = "chitrakumawat33@gmail.com"
    
    try:
        cur.execute("SELECT id, email FROM auth.users WHERE email = %s", (email,))
        result = cur.fetchone()
        if result:
            print(f"\nFOUND in auth.users: ID={result[0]}, Email={result[1]}")
            cur.execute("DELETE FROM auth.users WHERE email = %s", (email,))
            print("DELETED from auth.users!")
            conn.commit()
        else:
            print(f"\nNot found in auth.users")
    except Exception as e:
        print(f"\nCannot access auth.users: {e}")
    
    # Also check public.users
    try:
        cur.execute("SELECT id, email FROM public.users WHERE email = %s", (email,))
        result = cur.fetchone()
        if result:
            print(f"\nFOUND in public.users: ID={result[0]}, Email={result[1]}")
            cur.execute("DELETE FROM public.users WHERE email = %s", (email,))
            print("DELETED from public.users!")
            conn.commit()
        else:
            print(f"\nNot found in public.users")
    except Exception as e:
        print(f"Cannot access public.users: {e}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
