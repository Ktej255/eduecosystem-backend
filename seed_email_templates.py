"""
Seed default email templates into the database
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal
from app.models.email_notification import EmailTemplate, NotificationType


def create_default_templates():
    """Create system email templates"""
    db = SessionLocal()

    templates = [
        {
            "name": "course_enrollment",
            "display_name": "Course Enrollment Welcome",
            "subject": "Welcome to {{course_title}}!",
            "body_html": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #4CAF50;">Welcome to {{course_title}}!</h2>
                    <p>Hi {{student_name}},</p>
                    <p>Congratulations! You've successfully enrolled in <strong>{{course_title}}</strong>.</p>
                    <p><strong>Course Description:</strong><br>{{course_description}}</p>
                    <p><strong>Instructor:</strong> {{instructor_name}}</p>
                    <p>Get started with your learning journey today!</p>
                    <p style="margin-top: 30px;">
                        <a href="{{course_url}}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Go to Course</a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this email because you enrolled in a course on our platform.
                    </p>
                </body>
                </html>
            """,
            "body_text": "Hi {{student_name}},\n\nCongratulations! You've successfully enrolled in {{course_title}}.\n\nInstructor: {{instructor_name}}\n\nGet started with your learning journey today!",
            "variables": [
                "student_name",
                "course_title",
                "course_description",
                "instructor_name",
                "course_url",
            ],
            "notification_type": NotificationType.ENROLLMENT,
            "is_system": True,
        },
        {
            "name": "assignment_submitted",
            "display_name": "Assignment Submission Confirmation",
            "subject": "Assignment Submitted: {{assignment_title}}",
            "body_html": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #2196F3;">Assignment Submitted Successfully</h2>
                    <p>Hi {{student_name}},</p>
                    <p>Your assignment <strong>{{assignment_title}}</strong> has been successfully submitted.</p>
                    <p><strong>Submitted at:</strong> {{submitted_at}}</p>
                    <p>Your instructor will review your submission and provide feedback soon.</p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this email as a confirmation of your assignment submission.
                    </p>
                </body>
                </html>
            """,
            "body_text": "Hi {{student_name}},\n\nYour assignment {{assignment_title}} has been successfully submitted at {{submitted_at}}.\n\nYour instructor will review it soon.",
            "variables": ["student_name", "assignment_title", "submitted_at"],
            "notification_type": NotificationType.ASSIGNMENT_SUBMITTED,
            "is_system": True,
        },
        {
            "name": "assignment_graded",
            "display_name": "Assignment Graded Notification",
            "subject": "Your Assignment Has Been Graded: {{assignment_title}}",
            "body_html": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #FF9800;">Assignment Graded</h2>
                    <p>Hi {{student_name}},</p>
                    <p>Your assignment <strong>{{assignment_title}}</strong> has been graded.</p>
                    <p><strong>Your Grade:</strong> {{grade}}/{{max_grade}}</p>
                    <p>View detailed feedback and your submission in the course dashboard.</p>
                    <p style="margin-top: 30px;">
                        <a href="{{assignment_url}}" style="background-color: #FF9800; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">View Assignment</a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this email because your assignment was graded.
                    </p>
                </body>
                </html>
            """,
            "body_text": "Hi {{student_name}},\n\nYour assignment {{assignment_title}} has been graded.\n\nYour Grade: {{grade}}/{{max_grade}}\n\nView detailed feedback in the course dashboard.",
            "variables": [
                "student_name",
                "assignment_title",
                "grade",
                "max_grade",
                "assignment_url",
            ],
            "notification_type": NotificationType.ASSIGNMENT_GRADED,
            "is_system": True,
        },
        {
            "name": "quiz_completed",
            "display_name": "Quiz Completion Confirmation",
            "subject": "Quiz Completed: {{quiz_title}}",
            "body_html": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #9C27B0;">Quiz Completed!</h2>
                    <p>Hi {{student_name}},</p>
                    <p>You've successfully completed <strong>{{quiz_title}}</strong>.</p>
                    <p><strong>Your Score:</strong> {{score}}/{{total_questions}}</p>
                    <p>Great job! Keep up the excellent work.</p>
                    <p style="margin-top: 30px;">
                        <a href="{{quiz_url}}" style="background-color: #9C27B0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Review Quiz</a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this email as a confirmation of quiz completion.
                    </p>
                </body>
                </html>
            """,
            "body_text": "Hi {{student_name}},\n\nYou've successfully completed {{quiz_title}}.\n\nYour Score: {{score}}/{{total_questions}}\n\nGreat job!",
            "variables": [
                "student_name",
                "quiz_title",
                "score",
                "total_questions",
                "quiz_url",
            ],
            "notification_type": NotificationType.QUIZ_COMPLETED,
            "is_system": True,
        },
        {
            "name": "certificate_earned",
            "display_name": "Certificate Earned",
            "subject": "🎉 Congratulations! You've Earned a Certificate",
            "body_html": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #FFD700;">🎉 Congratulations!</h2>
                    <p>Hi {{student_name}},</p>
                    <p>We're thrilled to inform you that you've successfully completed <strong>{{course_title}}</strong> and earned your certificate!</p>
                    <p><strong>Completion Date:</strong> {{completion_date}}</p>
                    <p>This is a significant achievement and demonstrates your commitment to learning.</p>
                    <p style="margin-top: 30px;">
                        <a href="{{certificate_url}}" style="background-color: #FFD700; color: #333; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Download Certificate</a>
                    </p>
                    <p>Share your achievement on social media and with your professional network!</p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this email because you earned a certificate on our platform.
                    </p>
                </body>
                </html>
            """,
            "body_text": "Hi {{student_name}},\n\nCongratulations! You've successfully completed {{course_title}} and earned your certificate!\n\nCompletion Date: {{completion_date}}\n\nDownload your certificate: {{certificate_url}}",
            "variables": [
                "student_name",
                "course_title",
                "completion_date",
                "certificate_url",
            ],
            "notification_type": NotificationType.CERTIFICATE_EARNED,
            "is_system": True,
        },
        {
            "name": "course_announcement",
            "display_name": "Course Announcement",
            "subject": "📢 {{announcement_title}}",
            "body_html": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #F44336;">📢 {{announcement_title}}</h2>
                    <p>Hi {{student_name}},</p>
                    <p>Your instructor <strong>{{instructor_name}}</strong> has posted a new announcement:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #F44336; margin: 20px 0;">
                        {{announcement_content}}
                    </div>
                    <p style="margin-top: 30px;">
                        <a href="{{course_url}}" style="background-color: #F44336; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">View Course</a>
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        You're receiving this email because you're enrolled in this course.
                    </p>
                </body>
                </html>
            """,
            "body_text": "Hi {{student_name}},\n\nYour instructor {{instructor_name}} has posted a new announcement:\n\n{{announcement_title}}\n\n{{announcement_content}}",
            "variables": [
                "student_name",
                "instructor_name",
                "announcement_title",
                "announcement_content",
                "course_url",
            ],
            "notification_type": NotificationType.ANNOUNCEMENT,
            "is_system": True,
        },
    ]

    created_count = 0
    for template_data in templates:
        # Check if template already exists
        existing = (
            db.query(EmailTemplate)
            .filter(EmailTemplate.name == template_data["name"])
            .first()
        )

        if not existing:
            template = EmailTemplate(**template_data)
            db.add(template)
            created_count += 1
            print(f"✓ Created template: {template_data['display_name']}")
        else:
            print(f"⊘ Template already exists: {template_data['display_name']}")

    db.commit()
    db.close()

    print(f"\n✅ Successfully created {created_count} email templates!")
    return created_count


if __name__ == "__main__":
    print("Seeding default email templates...")
    create_default_templates()
