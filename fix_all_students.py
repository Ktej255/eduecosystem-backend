"""Fix all student accounts - set is_active and is_approved to True."""
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
    
    # First, show all users
    print("=== Current Users ===")
    cur.execute("SELECT id, email, role, is_active, is_approved FROM public.users ORDER BY id")
    for u in cur.fetchall():
        print(f"ID:{u[0]} Email:{u[1]} Role:{u[2]} Active:{u[3]} Approved:{u[4]}")
    
    # Update all students to be active and approved
    print("\n=== Fixing student accounts ===")
    cur.execute("""
        UPDATE public.users 
        SET is_active = TRUE, is_approved = TRUE 
        WHERE role = 'student'
        RETURNING id, email
    """)
    fixed = cur.fetchall()
    print(f"Fixed {len(fixed)} student accounts:")
    for f in fixed:
        print(f"  - {f[1]} (ID: {f[0]})")
    
    conn.commit()
    print("\n=== Done! All student accounts are now active and approved ===")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
