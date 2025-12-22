from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Boolean,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class CertificateTemplate(Base):
    """
    Certificate template model for customizable course completion certificates.
    Allows instructors to create and customize certificate designs.
    """

    __tablename__ = "certificate_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text)

    # Design elements
    background_url = Column(String)  # URL to background image
    background_color = Column(String, default="#ffffff")  # Hex color

    # Layout configuration (JSON)
    # Example: {"title": {"x": 100, "y": 200, "fontSize": 48, "fontFamily": "Arial", "color": "#000000"}}
    layout = Column(JSON, default=dict)

    # Typography
    title_font = Column(String, default="Arial")
    title_font_size = Column(Integer, default=48)
    title_color = Column(String, default="#000000")

    body_font = Column(String, default="Arial")
    body_font_size = Column(Integer, default=24)
    body_color = Column(String, default="#333333")

    # Border and styling
    border_style = Column(String, default="none")  # none, simple, ornate
    border_color = Column(String, default="#000000")

    # Logo/Seal
    logo_url = Column(String)
    signature_url = Column(String)

    # Template metadata
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)  # Can be used by other instructors

    # Creator
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    certificates = relationship("Certificate", back_populates="template")

    def __repr__(self):
        return f"<CertificateTemplate {self.name}>"
