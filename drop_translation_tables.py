from app.db.session import SessionLocal
from sqlalchemy import text


def drop_tables():
    db = SessionLocal()
    try:
        print("Dropping translation tables...")
        db.execute(text("DROP TABLE IF EXISTS user_language_preferences"))
        db.execute(text("DROP TABLE IF EXISTS content_translations"))
        db.execute(text("DROP TABLE IF EXISTS translations"))
        db.execute(text("DROP TABLE IF EXISTS languages"))
        db.commit()
        print("Tables dropped successfully.")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    drop_tables()
