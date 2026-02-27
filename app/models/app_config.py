from sqlalchemy import Column, Integer, String, JSON
from app.db.session import Base

class AppConfig(Base):
    """
    Global application configuration settings stored dynamically in the database.
    Used for live links, toggles, and UI configurations.
    """
    __tablename__ = "app_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(String, nullable=True)
