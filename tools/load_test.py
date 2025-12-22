"""
Load Testing with Locust
Tests system performance with multiple concurrent users
"""

from locust import HttpUser, task, between
import random


class EduEcosystemUser(HttpUser):
    """Simulates a typical user on the platform"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login before starting tasks"""
        # Register or login a test user
        email = f"loadtest{random.randint(1, 10000)}@example.com"
        password = "LoadTest123!"
        
        # Try to register
        self.client.post("/api/v1/login/register", json={
            "email": email,
            "password": password,
            "full_name": "Load Test User"
        })
        
        # Login to get token
        response = self.client.post("/api/v1/login/access-token", data={
            "username": email,
            "password": password
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        """View user dashboard - most common action"""
        self.client.get("/api/v1/users/me", headers=self.headers)
    
    @task(2)
    def browse_courses(self):
        """Browse available courses"""
        self.client.get("/api/v1/courses/", headers=self.headers)
    
    @task(1)
    def view_course_details(self):
        """View specific course details"""
        # Assume course IDs 1-10 exist
        course_id = random.randint(1, 10)
        self.client.get(f"/api/v1/courses/{course_id}", headers=self.headers)
    
    @task(1)
    def check_analytics(self):
        """Check user analytics"""
        self.client.get("/api/v1/analytics/student", headers=self.headers)
    
    @task(1)
    def view_community(self):
        """Visit community features"""
        self.client.get("/api/v1/social/wolf-packs", headers=self.headers)


class AdminUser(HttpUser):
    """Simulates admin/instructor usage"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as admin"""
        # Use a pre-created admin account
        response = self.client.post("/api/v1/login/access-token", data={
            "username": "admin@example.com",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(2)
    def view_analytics(self):
        """View instructor analytics"""
        self.client.get("/api/v1/analytics/instructor", headers=self.headers)
    
    @task(1)
    def manage_courses(self):
        """View courses for management"""
        self.client.get("/api/v1/courses/", headers=self.headers)


# To run:
# locust -f load_test.py --host=http://localhost:8000
# Then open http://localhost:8089 and configure:
# - Number of users: 50
# - Spawn rate: 5 users/second
# - Host: http://localhost:8000
