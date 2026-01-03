import sqlite3
from datetime import datetime

conn = sqlite3.connect('eduecosystem_v2.db')
cursor = conn.cursor()

# Insert a test user
cursor.execute("""
    INSERT INTO users (email, username, full_name, hashed_password, is_active, is_approved, role)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", ('test@example.com', 'testuser', 'Test User', 'hashed_password_placeholder', 1, 1, 'student'))

user_id = cursor.lastrowid
print(f"Created test user with id: {user_id}")

# Insert a test study session
cursor.execute("""
    INSERT INTO study_sessions (user_id, topic_name, session_type, start_time, end_time, duration_seconds, comprehension_score)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (user_id, 'Test Topic', 'study_25', datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), 1500, 85))

session_id = cursor.lastrowid
print(f"Created test study session with id: {session_id}")

conn.commit()

# Verify
cursor.execute("SELECT * FROM study_sessions WHERE id = ?", (session_id,))
row = cursor.fetchone()
print(f"Study session row: {row}")

conn.close()
print("Test data created successfully!")
