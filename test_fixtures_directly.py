#!/usr/bin/env python
"""
Direct test of the peer review test to diagnose the error
"""

import sys
import os
import traceback

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

print("Step 1: Importing dependencies...")
try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    print("✓ Core dependencies imported")
except Exception as e:
    print(f"✗ Error importing core dependencies: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Importing app components...")
try:
    from app.db.session import Base
    import app.models
    from main import app

    print("✓ App components imported")
except Exception as e:
    print(f"✗ Error importing app components: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Creating test database...")
try:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Test database created")
except Exception as e:
    print(f"✗ Error creating test database: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Creating test session and client...")
try:
    db = TestingSessionLocal()
    from app.api.deps import get_db as api_get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[api_get_db] = override_get_db
    client = TestClient(app)
    print("✓ Test client created")
except Exception as e:
    print(f"✗ Error creating test client: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 5: Testing fixture functions...")
try:
    from app.tests.utils.user import create_random_user
    from app.tests.utils.course import create_random_course
    from app.tests.utils.assignment import create_random_assignment

    print("✓ Utility functions imported")

    # Test creating users
    instructor = create_random_user(db)
    instructor.role = "instructor"
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    print(f"✓ Created instructor: {instructor.email}")

    student1 = create_random_user(db, role="student")
    print(f"✓ Created student1: {student1.email}")

    student2 = create_random_user(db, role="student")
    print(f"✓ Created student2: {student2.email}")

    # Test creating course and assignment
    course = create_random_course(db, instructor_id=instructor.id)
    print(f"✓ Created course: {course.title}")

    assignment = create_random_assignment(db, course_id=course.id)
    print(f"✓ Created assignment: {assignment.title}")

except Exception as e:
    print(f"✗ Error in fixtures: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS: All fixture setup steps passed!")
print("=" * 60)
print("\nThe peer review test should be able to run now.")
print("If pytest still fails, the error is likely in pytest configuration,")
print("not in the test code or fixtures themselves.")
