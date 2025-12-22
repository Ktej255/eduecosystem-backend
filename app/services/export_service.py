"""
Export Service

Service for exporting data in various formats (CSV, PDF, JSON).
"""

import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

from app.models.user import User
from app.models.course import Course
from app.models.lesson_progress import LessonProgress as Progress


class ExportService:
    """Service for data exports"""

    @staticmethod
    def generate_csv(
        data: List[Dict[str, Any]], headers: Optional[List[str]] = None
    ) -> str:
        """
        Generate CSV from list of dictionaries.

        Args:
            data: List of dictionaries
            headers: Optional list of headers (uses first dict keys if not provided)

        Returns:
            CSV string
        """
        if not data:
            return ""

        output = io.StringIO()

        # Use provided headers or extract from first dict
        fieldnames = headers or list(data[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    @staticmethod
    def generate_pdf(
        data: List[Dict[str, Any]], title: str, headers: Optional[List[str]] = None
    ) -> bytes:
        """
        Generate PDF from list of dictionaries.

        Args:
            data: List of dictionaries
            title: PDF title
            headers: Optional list of headers

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Styles
        styles = getSampleStyleSheet()

        # Title
        title_style = styles["Heading1"]
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.25 * inch))

        # Metadata
        timestamp_style = styles["Normal"]
        timestamp = (
            f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        elements.append(Paragraph(timestamp, timestamp_style))
        elements.append(Spacer(1, 0.5 * inch))

        if not data:
            elements.append(Paragraph("No data available", styles["Normal"]))
        else:
            # Create table
            fieldnames = headers or list(data[0].keys())

            # Table data
            table_data = [fieldnames]
            for row in data:
                table_data.append([str(row.get(field, "")) for field in fieldnames])

            # Create table
            table = Table(table_data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            elements.append(table)

        # Build PDF
        doc.build(elements)

        return buffer.getvalue()

    @staticmethod
    def export_analytics(
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "csv",
    ) -> str | bytes:
        """
        Export user analytics data.

        Args:
            db: Database session
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            format: Export format ('csv', 'pdf', 'json')

        Returns:
            Exported data as string (CSV/JSON) or bytes (PDF)
        """
        from app.models.analytics import CourseAnalytics

        # Get analytics data
        query = db.query(CourseAnalytics).filter(CourseAnalytics.user_id == user_id)

        if start_date:
            query = query.filter(CourseAnalytics.created_at >= start_date)
        if end_date:
            query = query.filter(CourseAnalytics.created_at <= end_date)

        analytics = query.all()

        # Convert to dict
        data = []
        for item in analytics:
            data.append(
                {
                    "course_id": item.course_id,
                    "date": item.created_at.isoformat() if item.created_at else "",
                    "lessons_completed": item.lessons_completed,
                    "quizzes_taken": item.quizzes_taken,
                    "time_spent_minutes": item.time_spent,
                    "engagement_score": item.engagement_score,
                }
            )

        if format == "csv":
            return ExportService.generate_csv(data)
        elif format == "pdf":
            return ExportService.generate_pdf(
                data, f"Analytics Report - User {user_id}"
            )
        elif format == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def export_course_content(
        db: Session, course_id: int, format: str = "json"
    ) -> str | bytes:
        """
        Export course content for backup.

        Args:
            db: Database session
            course_id: Course ID
            format: Export format ('json', 'pdf')

        Returns:
            Exported course data
        """
        course = db.query(Course).filter(Course.id == course_id).first()

        if not course:
            raise ValueError("Course not found")

        # Build course data structure
        data = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "price": float(course.price) if course.price else 0,
            "created_at": course.created_at.isoformat() if course.created_at else "",
            "updated_at": course.updated_at.isoformat() if course.updated_at else "",
            "modules": [],
        }

        # Add modules and lessons (if relationships exist)
        if hasattr(course, "modules"):
            for module in course.modules:
                module_data = {
                    "id": module.id,
                    "title": module.title,
                    "description": module.description,
                    "order": module.order_index,
                    "lessons": [],
                }

                if hasattr(module, "lessons"):
                    for lesson in module.lessons:
                        lesson_data = {
                            "id": lesson.id,
                            "title": lesson.title,
                            "content_type": lesson.content_type,
                            "duration": lesson.duration,
                            "order": lesson.order_index,
                        }
                        module_data["lessons"].append(lesson_data)

                data["modules"].append(module_data)

        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "pdf":
            # Simplified course overview for PDF
            summary_data = [
                {"Field": "Title", "Value": data["title"]},
                {"Field": "Category", "Value": data["category"]},
                {"Field": "Modules", "Value": len(data["modules"])},
                {"Field": "Price", "Value": f"${data['price']}"},
            ]
            return ExportService.generate_pdf(
                summary_data, f"Course Export - {data['title']}"
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def export_user_data(
        db: Session, user_id: int, format: str = "json"
    ) -> str | bytes:
        """
        Export user data for GDPR compliance.

        Args:
            db: Database session
            user_id: User ID
            format: Export format ('json', 'pdf')

        Returns:
            Exported user data
        """
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise ValueError("User not found")

        # Get user progress
        progress_records = db.query(Progress).filter(Progress.user_id == user_id).all()

        # Build user data
        data = {
            "personal_information": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat() if user.created_at else "",
            },
            "account_status": {
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
            },
            "progress": [],
        }

        # Add progress data
        for progress in progress_records:
            data["progress"].append(
                {
                    "course_id": progress.course_id,
                    "lesson_id": progress.lesson_id,
                    "completed": progress.completed,
                    "progress_percentage": progress.progress_percentage,
                    "last_accessed": progress.last_accessed_at.isoformat()
                    if progress.last_accessed_at
                    else "",
                }
            )

        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "pdf":
            # User summary for PDF
            summary_data = [
                {"Field": "Email", "Value": user.email},
                {"Field": "Full Name", "Value": user.full_name or "N/A"},
                {
                    "Field": "Account Created",
                    "Value": user.created_at.strftime("%Y-%m-%d")
                    if user.created_at
                    else "N/A",
                },
                {"Field": "Courses Enrolled", "Value": len(progress_records)},
            ]
            return ExportService.generate_pdf(summary_data, "User Data Export (GDPR)")
        else:
            raise ValueError(f"Unsupported format: {format}")
