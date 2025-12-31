"""
Direct RDS Debug Script - Bypass all application logic
"""
import psycopg2
from passlib.context import CryptContext

# Production RDS credentials from apprunner.yaml
DB_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def debug_user(email):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute("""
            SELECT id, email, hashed_password, is_active, is_approved, role, token_version
            FROM users 
            WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        
        if user:
            user_id, email, hashed_password, is_active, is_approved, role, token_version = user
            print(f"\n=== USER FOUND ===")
            print(f"ID: {user_id}")
            print(f"Email: {email}")
            print(f"Is Active: {is_active}")
            print(f"Is Approved: {is_approved}")
            print(f"Role: {role}")
            print(f"Token Version: {token_version}")
            print(f"Password Hash (first 30): {hashed_password[:30] if hashed_password else 'NULL'}...")
            
            # Test password verification
            test_passwords = ["chitrakumawat@33", "Student@123", "chitrakumawat33"]
            print(f"\n=== PASSWORD TESTS ===")
            for pwd in test_passwords:
                if hashed_password:
                    result = pwd_context.verify(pwd, hashed_password)
                    print(f"  '{pwd}' -> {result}")
                else:
                    print(f"  '{pwd}' -> NO HASH TO CHECK")
        else:
            print(f"\n=== USER NOT FOUND: {email} ===")
            
            # List all users
            cursor.execute("SELECT id, email, is_active, is_approved FROM users ORDER BY id")
            all_users = cursor.fetchall()
            print(f"\n=== ALL USERS IN DATABASE ({len(all_users)}) ===")
            for u in all_users:
                print(f"  {u[0]}: {u[1]} | Active: {u[2]} | Approved: {u[3]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_user("chitrakumawat33@gmail.com")
