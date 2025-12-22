"""
Quick script to update user role to instructor
"""

import sqlite3

# Connect to database
conn = sqlite3.connect("eduecosystem.db")
cursor = conn.cursor()

# Update user role
cursor.execute(
    "UPDATE users SET role = 'instructor' WHERE email = 'instructor@test.com'"
)
conn.commit()

# Verify the change
cursor.execute(
    "SELECT email, role, full_name FROM users WHERE email = 'instructor@test.com'"
)
user = cursor.fetchone()

if user:
    print("✅ Successfully updated user role!")
    print(f"   Email: {user[0]}")
    print(f"   Role: {user[1]}")
    print(f"   Name: {user[2]}")
else:
    print("❌ User not found")

conn.close()

print("\n🔄 Next steps:")
print("1. Go to http://localhost:3000")
print("2. Logout (if logged in)")
print("3. Login again as instructor@test.com / password123")
print("4. Navigate to 'Create Course' - it will now work!")
