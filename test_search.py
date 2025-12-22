from app.db.session import SessionLocal
from app.models.user import User

db = SessionLocal()
query = "Test"
users = (
    db.query(User)
    .filter((User.full_name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
    .all()
)

print(f"Found {len(users)} users matching '{query}':")
for user in users:
    print(f" - {user.full_name} ({user.email})")
