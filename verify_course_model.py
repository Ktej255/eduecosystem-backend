import sys
import os

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import Base
from app.models.course import Course
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def verify_course():
    print("Verifying Course model...")
    try:
        # Create in-memory DB
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Try to instantiate Course with slug
        try:
            course = Course(
                title="Test Course",
                slug="test-course",
                description="Description",
                instructor_id=1,
            )
            print("Successfully instantiated Course with slug.")
        except TypeError as e:
            print(f"FAILED to instantiate Course: {e}")
            # Check columns
            print("Course columns:", Course.__table__.columns.keys())
            return

        session.add(course)
        # We won't commit because instructor doesn't exist, but instantiation is what we care about.
        print("Verification passed.")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_course()
