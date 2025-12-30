"""Check ALL user tables in Supabase and delete from all of them."""
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
    
    # Check ALL schemas for users tables
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name = 'users'
    """)
    tables = cur.fetchall()
    print("All 'users' tables found:")
    for t in tables:
        print(f"  {t[0]}.{t[1]}")
    
    # Check for this email in ALL tables
    email = "chitrakumawat33@gmail.com"
    print(f"\nSearching for {email} in all tables:")
    
    for schema, table in tables:
        try:
            cur.execute(f"SELECT id, email FROM {schema}.{table} WHERE email = %s", (email,))
            result = cur.fetchone()
            if result:
                print(f"  FOUND in {schema}.{table}: ID={result[0]}")
                # Delete it
                cur.execute(f"DELETE FROM {schema}.{table} WHERE email = %s", (email,))
                print(f"  DELETED from {schema}.{table}")
        except Exception as e:
            print(f"  Error checking {schema}.{table}: {e}")
    
    conn.commit()
    print("\n✅ Done! User should now be deletable.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
