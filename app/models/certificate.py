from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import secrets


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    enrollment_id = Column(
        Integer, ForeignKey("enrollments.id"), nullable=False, unique=True
    )

    # Certificate details
    certificate_number = Column(String, unique=True, nullable=False, index=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Student info (denormalized for certificate permanence)
    student_name = Column(String, nullable=False)
    student_email = Column(String, nullable=False)

    # Course info (denormalized)
    course_title = Column(String, nullable=False)
    instructor_name = Column(String, nullable=False)

    # PDF storage
    pdf_url = Column(String, nullable=True)

    # Metadata
    completion_percentage = Column(Float, default=100.0)
    total_lessons_completed = Column(Integer, default=0)
    time_spent_hours = Column(Float, default=0.0)

    # Template reference (optional - can use default template)
    template_id = Column(Integer, ForeignKey("certificate_templates.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="certificates")
    course = relationship("Course", back_populates="certificates")
    enrollment = relationship("Enrollment", back_populates="certificate")
    template = relationship("CertificateTemplate", back_populates="certificates")

    def __repr__(self):
        return f"<Certificate {self.certificate_number} - {self.student_name}>"

    @staticmethod
    def generate_certificate_number():
        """Generate unique certificate number: CERT-YYYY-XXXXXX"""
        year = datetime.now().year
        random_suffix = secrets.token_hex(3).upper()  # 6 chars
        return f"CERT-{year}-{random_suffix}"
