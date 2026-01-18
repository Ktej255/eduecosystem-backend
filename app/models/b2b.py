from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    domain = Column(String, unique=True, index=True) # e.g., @acme.com
    subscription_plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship("OrganizationMember", back_populates="organization")

class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="employee") # admin, employee, manager
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="members")
    user = relationship("User")
