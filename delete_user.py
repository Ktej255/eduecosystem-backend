"""Delete the user account so it can be recreated fresh."""
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
    
    # Delete the user
    cur.execute("DELETE FROM public.users WHERE email = %s RETURNING id, email", 
                ("chitrakumawat33@gmail.com",))
    
    result = cur.fetchone()
    if result:
        print(f"✅ Deleted user: {result[1]} (ID: {result[0]})")
        conn.commit()
    else:
        print("User not found (may already be deleted)")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
