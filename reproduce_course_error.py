import sys
import os

sys.path.append(os.getcwd())

from app.models.course import Course


def test_course_instantiation():
    try:
        print("Attempting to instantiate Course...")
        course = Course(
            title="Test Course",
            slug="test-course",
            description="Test Description",
            instructor_id=1,
            price=100.0,
            is_published=True,
        )
        print("Course instantiated successfully:", course)
    except Exception as e:
        print(f"Error instantiating Course: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_course_instantiation()
