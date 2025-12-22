from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class TwoFactorAuth(Base):
    """Two-Factor Authentication configuration for users"""

    __tablename__ = "two_factor_auth"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    secret = Column(String(255), nullable=False)  # Encrypted TOTP secret
    is_enabled = Column(Boolean, default=False, nullable=False)
    verified_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When setup was completed
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="two_factor_auth")
    backup_codes = relationship(
        "TwoFactorBackupCode", back_populates="two_factor", cascade="all, delete-orphan"
    )


class TwoFactorBackupCode(Base):
    """Backup recovery codes for 2FA"""

    __tablename__ = "two_factor_backup_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    two_factor_auth_id = Column(
        Integer, ForeignKey("two_factor_auth.id"), nullable=False, index=True
    )
    code_hash = Column(String(255), nullable=False)  # Bcrypt hash of the code
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="backup_codes")
    two_factor = relationship("TwoFactorAuth", back_populates="backup_codes")
