"""Check columns and update user with available fields."""
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
    
    # Check user columns
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    columns = [row[0] for row in cur.fetchall()]
    print("User table columns:", columns)
    
    # Update only available columns
    new_hash = pwd_context.hash("chitrakumawat@33")
    
    # Build update based on available columns
    update_fields = {
        'hashed_password': new_hash,
        'role': 'student',
        'is_active': True,
        'is_superuser': False,
    }
    
    # Add optional fields if they exist
    if 'is_approved' in columns:
        update_fields['is_approved'] = True
    
    # Build SQL
    set_clause = ', '.join([f"{k} = %s" for k in update_fields.keys()])
    values = list(update_fields.values()) + ["chitrakumawat33@gmail.com"]
    
    cur.execute(f"""
        UPDATE users SET {set_clause}
        WHERE email = %s
        RETURNING id, email, role, is_active
    """, values)
    
    result = cur.fetchone()
    if result:
        print(f"\n✅ Updated user:")
        print(f"   ID: {result[0]}")
        print(f"   Email: {result[1]}")
        print(f"   Role: {result[2]}")
        print(f"   Is Active: {result[3]}")
        conn.commit()
        print("\n✅ User is now ready for login!")
    else:
        print("❌ User not found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()
