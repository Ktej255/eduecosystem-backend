import time
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User
from app.models.drill import DrillSession
from app.models.meditation import MeditationSession
from app.models.activity_log import ActivityLog
from app.api.api_v1.endpoints.admin_student_insights import get_at_risk_students

# Setup SQLite for benchmarking
SQLALCHEMY_DATABASE_URL = "sqlite:///./benchmark.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_benchmark_data(db, num_students=200):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    students = []
    for i in range(num_students):
        student = User(
            email=f"student{i}@example.com",
            username=f"student{i}",
            hashed_password="hashed_password",
            full_name=f"Student {i}",
            role="student",
            is_active=True
        )
        db.add(student)
        students.append(student)

    db.commit()
    for s in students:
        db.refresh(s)

    now = datetime.utcnow()

    for i, student in enumerate(students):
        # Academic Risk: 50% students have low scores
        score = 40 if i % 2 == 0 else 70
        for _ in range(5):
            db.add(DrillSession(student_id=student.id, overall_score=score, date=(now - timedelta(days=1)).date(), question_number=1))

        # Wellness Risk: 50% students haven't meditated in 4 days
        meditation_date = now - timedelta(days=4) if i % 2 == 1 else now - timedelta(days=1)
        db.add(MeditationSession(user_id=student.id, created_at=meditation_date))

        # Churn Risk: 50% students inactive for 6 days
        activity_date = now - timedelta(days=6) if i % 4 == 0 else now - timedelta(days=1)
        db.add(ActivityLog(user_id=student.id, timestamp=activity_date, action="test"))

    db.commit()
    return students

def run_benchmark():
    db = TestingSessionLocal()
    try:
        setup_benchmark_data(db)

        # Warm up
        get_at_risk_students(db, current_admin=None)

        start_time = time.time()
        results = get_at_risk_students(db, current_admin=None)
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"Execution Time: {execution_time:.4f} seconds")
        print(f"Number of at-risk students found: {len(results)}")

        # Save results for correctness check later
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)

        return execution_time
    finally:
        db.close()

if __name__ == "__main__":
    run_benchmark()
