import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@example.com"
PASSWORD = "admin"


def get_token():
    response = requests.post(
        f"{BASE_URL}/login/access-token", data={"username": EMAIL, "password": PASSWORD}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]


def test_quiz_flow():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("1. Creating interactive quiz...")
    quiz_data = {
        "title": "Interactive Python Quiz",
        "description": "Test your Python skills",
        "course_id": 1,  # Assuming course 1 exists
        "time_limit_minutes": 10,
        "passing_score": 70.0,
        "is_published": True,
        "instant_feedback": True,
        "show_hints": True,
        "enable_ai_grading": True,
        "questions": [
            {
                "text": "What is 2 + 2?",
                "type": "multiple_choice",
                "points": 10,
                "explanation": "Basic math",
                "options": [
                    {"text": "4", "is_correct": True},
                    {"text": "5", "is_correct": False},
                ],
            },
            {
                "text": "Python is a compiled language.",
                "type": "true_false",
                "points": 5,
                "options": [
                    {"text": "True", "is_correct": False},
                    {"text": "False", "is_correct": True},
                ],
            },
        ],
    }

    # We need a valid course_id. Let's try to get one or create one.
    # For now, let's assume course 1 exists or use a try/except
    try:
        response = requests.post(
            f"{BASE_URL}/quizzes/", json=quiz_data, headers=headers
        )
        if response.status_code == 404:  # Course not found
            print(
                "Course 1 not found, skipping creation test or need to create course first."
            )
            return
        elif response.status_code != 201:
            print(f"Failed to create quiz: {response.text}")
            return

        quiz = response.json()
        quiz_id = quiz["id"]
        print(f"Quiz created: {quiz_id}")

        # Add feedback to question 1
        q1_id = quiz["questions"][0]["id"]
        print(f"Adding feedback to question {q1_id}...")
        feedback_data = {
            "question_id": q1_id,
            "feedback_text": "Good job!",
            "feedback_for_correct": "You know your math!",
            "feedback_for_incorrect": "Try counting on fingers.",
            "hint_text": "It's an even number.",
        }
        response = requests.post(
            f"{BASE_URL}/quiz-feedback/", json=feedback_data, headers=headers
        )
        if response.status_code == 201:
            print("Feedback added.")
        else:
            print(f"Failed to add feedback: {response.text}")

        print("2. Starting quiz attempt...")
        response = requests.post(f"{BASE_URL}/quizzes/{quiz_id}/start", headers=headers)
        if response.status_code != 200:
            print(f"Failed to start quiz: {response.text}")
            return

        attempt_data = response.json()
        attempt_id = attempt_data["attempt_id"]
        questions = attempt_data["questions"]
        print(f"Attempt started: {attempt_id}")

        print("3. Submitting answer for Question 1 (Correct)...")
        q1 = questions[0]
        # Find correct option
        # In real quiz, client doesn't know correct option, but here we do from creation
        # Wait, the start response doesn't include is_correct for options.
        # So we have to guess or use the order we created.
        # We created "4" as correct.
        # Let's find option with text "4"
        opt_correct = next(o for o in q1["options"] if o["text"] == "4")

        ans_data = {
            "question_id": q1["id"],
            "selected_option_id": opt_correct["id"],
            "time_spent_seconds": 5,
        }
        response = requests.post(
            f"{BASE_URL}/quizzes/attempts/{attempt_id}/submit-answer",
            json=ans_data,
            headers=headers,
        )
        result = response.json()
        print(
            f"Result: Correct={result['is_correct']}, Feedback={result.get('feedback', {}).get('feedback_text')}"
        )

        print("4. Submitting answer for Question 2 (Incorrect)...")
        q2 = questions[1]
        # Correct is False. Let's pick True (incorrect)
        opt_incorrect = next(o for o in q2["options"] if o["text"] == "True")

        ans_data = {
            "question_id": q2["id"],
            "selected_option_id": opt_incorrect["id"],
            "time_spent_seconds": 10,
        }
        response = requests.post(
            f"{BASE_URL}/quizzes/attempts/{attempt_id}/submit-answer",
            json=ans_data,
            headers=headers,
        )
        result = response.json()
        print(f"Result: Correct={result['is_correct']}")

        print("5. Completing quiz...")
        comp_data = {"difficulty_rating": 2.0, "confidence_score": 0.9}
        response = requests.post(
            f"{BASE_URL}/quizzes/attempts/{attempt_id}/complete",
            json=comp_data,
            headers=headers,
        )
        final_result = response.json()
        print(
            f"Quiz completed. Score: {final_result['score']}, Passed: {final_result['passed']}"
        )
        print(
            f"Analytics: Time Spent={final_result['attempt']['analytics']['time_spent_seconds']}s"
        )

        print("6. Reviewing quiz...")
        response = requests.get(
            f"{BASE_URL}/quizzes/attempts/{attempt_id}/review", headers=headers
        )
        review = response.json()
        print(f"Review retrieved. Questions reviewed: {len(review['questions'])}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_quiz_flow()
