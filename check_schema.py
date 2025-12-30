"""Check schemas and tables."""
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
    
    # List all tables that have 'user' in the name
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%user%'
        ORDER BY table_schema, table_name
    """)
    tables = cur.fetchall()
    print("Tables with 'user' in name:")
    for t in tables:
        print(f"  {t[0]}.{t[1]}")
    
    # Check public.users columns
    print("\n\nPublic.users columns:")
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'users'
        ORDER BY ordinal_position
    """)
    for col in cur.fetchall():
        print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
    
    # Get a sample user
    print("\n\nSample user:")
    cur.execute("SELECT * FROM public.users LIMIT 1")
    columns = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if row:
        for i, col in enumerate(columns):
            print(f"  {col}: {row[i]}")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
