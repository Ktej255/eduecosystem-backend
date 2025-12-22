from sqlalchemy import create_engine, inspect, text
from app.core.config import settings
import sys


def check_db():
    print(f"Checking database at: {settings.DATABASE_URL}")
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Found {len(tables)} tables:")
        for t in sorted(tables):
            print(f" - {t}")

        with engine.connect() as conn:
            try:
                version = conn.execute(text("SELECT * FROM alembic_version")).fetchall()
                print(f"Alembic Version: {version}")
            except Exception as e:
                print(f"Could not get alembic version: {e}")

    except Exception as e:
        print(f"Error connecting to DB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_db()
