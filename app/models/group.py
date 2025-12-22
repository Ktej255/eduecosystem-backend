from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base

# Association table for User-Group many-to-many relationship (optional, but let's keep it simple: One User -> One Group for now)
# Actually, "Wolf Pack" implies a single primary group. Let's do One-to-Many (Group has many Users).


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    avatar_url = Column(String, nullable=True)

    # Relationships
    members = relationship("User", back_populates="group")
