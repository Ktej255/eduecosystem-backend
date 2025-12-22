from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class LessonNote(Base):
    """Student notes for lessons"""

    __tablename__ = "lesson_notes"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=True)  # Optional note title
    content = Column(Text, nullable=False)

    # Positioning
    timestamp = Column(
        Integer, nullable=True
    )  # Video timestamp in seconds (if applicable)

    # Metadata
    is_private = Column(Boolean, default=True)  # Currently all notes are private
    color = Column(String(20), default="yellow")  # yellow, blue, green, red, purple

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", backref="student_notes")
    user = relationship("User", backref="lesson_notes")


class LessonBookmark(Base):
    """Student bookmarks for lessons"""

    __tablename__ = "lesson_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=False
    )  # Denormalized for easier queries

    # Optional note/description
    note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lesson = relationship("Lesson", backref="bookmarks")
    user = relationship("User", backref="lesson_bookmarks")
    course = relationship("Course", backref="lesson_bookmarks")

    # Unique constraint: one bookmark per user per lesson
    __table_args__ = ({"sqlite_autoincrement": True},)


class CourseBookmark(Base):
    """Student bookmarks for entire courses"""

    __tablename__ = "course_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course", backref="course_bookmarks")
    user = relationship("User", backref="course_bookmarks")

    # Unique constraint: one bookmark per user per course
    __table_args__ = ({"sqlite_autoincrement": True},)
