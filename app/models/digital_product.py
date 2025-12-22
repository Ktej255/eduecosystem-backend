from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class DigitalProduct(Base):
    __tablename__ = "digital_products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String)  # PDF, ZIP, AUDIO, etc.
    is_active = Column(Boolean, default=True)
    
    # Metadata
    sales_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Owner
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instructor = relationship("User", backref="digital_products")
