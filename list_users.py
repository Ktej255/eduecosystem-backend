"""List all registered users."""
import psycopg2

conn = psycopg2.connect(
    host="aws-1-ap-south-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.ffzikovynwnnlettdzgw",
    password="Edueco2025!Secure"
)

cur = conn.cursor()
cur.execute("SELECT id, email, is_active, is_approved FROM public.users ORDER BY id")
users = cur.fetchall()
print(f"=== Total: {len(users)} users ===")
for u in users:
    print(f"ID:{u[0]} | Email:{u[1]} | Active:{u[2]} | Approved:{u[3]}")
conn.close()
