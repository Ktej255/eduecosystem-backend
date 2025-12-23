"""
Minimal script to create essential tables in production database.
"""
import os

# Set the DATABASE_URL to production
DATABASE_URL = "postgresql://postgres:Edueco123!@eduecosystem-prod.cw5ei40o4bwd.us-east-1.rds.amazonaws.com:5432/eduecosystem_prod"

from sqlalchemy import create_engine, text

def create_essential_tables():
    """Create the essential tables needed for login."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create users table
        print("Creating users table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(255) UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_superuser BOOLEAN DEFAULT FALSE,
                full_name VARCHAR(255),
                coins INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                token_version INTEGER DEFAULT 1,
                group_id INTEGER,
                role VARCHAR(50) DEFAULT 'student',
                last_login TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE,
                email_notifications BOOLEAN DEFAULT TRUE,
                is_approved BOOLEAN DEFAULT TRUE,
                is_premium BOOLEAN DEFAULT FALSE,
                stripe_customer_id VARCHAR(255),
                subscription_status VARCHAR(50) DEFAULT 'free',
                organization_id INTEGER,
                is_sso_user BOOLEAN DEFAULT FALSE,
                sso_external_id VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE
            )
        """))
        conn.commit()
        print("Users table created!")
        
        # Create groups table (required by users.group_id FK)
        print("Creating groups table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print("Groups table created!")
        
        # Check tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"\nTotal tables: {len(tables)}")
        for t in tables:
            print(f"  - {t}")

def create_admin_user():
    """Create the admin user."""
    print("\nCreating admin user...")
    
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if admin exists
        result = conn.execute(text("SELECT id FROM users WHERE email = 'ktej255@gmail.com'"))
        if result.fetchone():
            print("Admin user already exists!")
            return
        
        # Hash password
        hashed_password = pwd_context.hash("Tej@1106")
        
        # Create admin
        conn.execute(text("""
            INSERT INTO users (email, hashed_password, full_name, role, is_superuser, is_active, is_approved)
            VALUES ('ktej255@gmail.com', :password, 'Master Admin', 'admin', TRUE, TRUE, TRUE)
        """), {"password": hashed_password})
        conn.commit()
        print("Admin user created: ktej255@gmail.com")

if __name__ == "__main__":
    create_essential_tables()
    create_admin_user()
    print("\nDatabase initialization complete!")
