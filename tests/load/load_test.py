"""
Load Testing with Locust
Simulates realistic user behavior and load patterns
"""

from locust import HttpUser, task, between, TaskSet
import random


class StudentBehavior(TaskSet):
    """Student user behavior patterns"""

    @task(10)
    def browse_courses(self):
        """Browse course catalog"""
        self.client.get(
            "/api/v1/courses/", params={"skip": random.randint(0, 20), "limit": 20}
        )

    @task(5)
    def view_course_details(self):
        """View specific course"""
        course_id = random.randint(1, 50)
        self.client.get(f"/api/v1/courses/{course_id}")

    @task(3)
    def get_my_courses(self):
        """View enrolled courses"""
        self.client.get("/api/v1/enrollments/my-courses")

    @task(7)
    def view_progress(self):
        """Check progress"""
        course_id = random.randint(1, 10)
        self.client.get(f"/api/v1/progress/{course_id}")

    @task(2)
    def complete_lesson(self):
        """Complete a lesson"""
        lesson_id = random.randint(1, 100)
        self.client.post(f"/api/v1/progress/lessons/{lesson_id}/complete")

    @task(1)
    def take_quiz(self):
        """Submit quiz"""
        quiz_id = random.randint(1, 20)
        self.client.post(
            f"/api/v1/quizzes/{quiz_id}/submit",
            json={
                "answers": [
                    {"question_id": 1, "selected_option": 2},
                    {"question_id": 2, "selected_option": 1},
                ]
            },
        )

    @task(3)
    def view_achievements(self):
        """View achievements"""
        self.client.get("/api/v1/achievements")

    @task(2)
    def view_leaderboard(self):
        """View leaderboard"""
        self.client.get("/api/v1/gamification/leaderboard")

    @task(1)
    def view_challenges(self):
        """View challenges"""
        self.client.get("/api/v1/challenges")


class InstructorBehavior(TaskSet):
    """Instructor user behavior patterns"""

    @task(5)
    def view_my_courses(self):
        """View instructor courses"""
        self.client.get("/api/v1/courses/instructor/my-courses")

    @task(3)
    def view_course_analytics(self):
        """View course analytics"""
        course_id = random.randint(1, 10)
        self.client.get(f"/api/v1/analytics/courses/{course_id}")

    @task(2)
    def view_enrollments(self):
        """View course enrollments"""
        course_id = random.randint(1, 10)
        self.client.get(f"/api/v1/courses/{course_id}/enrollments")

    @task(1)
    def grade_assignment(self):
        """Grade assignment"""
        assignment_id = random.randint(1, 50)
        self.client.post(
            f"/api/v1/assignments/{assignment_id}/submissions/1/grade",
            json={"score": random.randint(70, 100), "feedback": "Good work!"},
        )


class StudentUser(HttpUser):
    """Student user simulation"""

    tasks = [StudentBehavior]
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "student@example.com", "password": "password123"},
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})


class InstructorUser(HttpUser):
    """Instructor user simulation"""

    tasks = [InstructorBehavior]
    wait_time = between(2, 8)

    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "instructor@example.com", "password": "password123"},
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})


# Load testing scenarios
"""
Run different load test scenarios:

1. Normal Load (100 users):
   locust -f load_test.py --host=http://localhost:8000 --users 100 --spawn-rate 10

2. Spike Test (500 users):
   locust -f load_test.py --host=http://localhost:8000 --users 500 --spawn-rate 50

3. Stress Test (1000 users):
   locust -f load_test.py --host=http://localhost:8000 --users 1000 --spawn-rate 100

4. Endurance Test (200 users for 1 hour):
   locust -f load_test.py --host=http://localhost:8000 --users 200 --spawn-rate 20 --run-time 1h

5. Headless mode with report:
   locust -f load_test.py --host=http://localhost:8000 --headless --users 200 --spawn-rate 20 --run-time 5m --html load-test-report.html
"""
