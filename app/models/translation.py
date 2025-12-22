"""
Translation Models

Database models for multi-language internationalization support.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.db.session import Base


class Language(Base):
    """
    Supported languages configuration.
    """

    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(10), unique=True, nullable=False, index=True
    )  # e.g., 'en', 'es', 'fr'
    name = Column(String(100), nullable=False)  # e.g., 'English', 'Español', 'Français'
    native_name = Column(
        String(100), nullable=False
    )  # e.g., 'English', 'Español', 'Français'
    is_rtl = Column(
        Boolean, default=False, nullable=False
    )  # Right-to-left languages (Arabic, Hebrew)
    is_active = Column(Boolean, default=True, nullable=False)
    flag_emoji = Column(String(10))  # e.g., '🇺🇸', '🇪🇸', '🇫🇷'
    sort_order = Column(Integer, default=0)  # For display ordering
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Translation(Base):
    """
    Stores translated content for UI strings and static content.
    Uses key-based translation system.
    """

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(
        String(255), nullable=False, index=True
    )  # e.g., 'course.title', 'button.submit'
    language_code = Column(String(10), nullable=False, index=True)  # e.g., 'en', 'es'
    value = Column(Text, nullable=False)  # Translated text
    namespace = Column(
        String(100), default="common", index=True
    )  # e.g., 'common', 'auth', 'course'
    description = Column(Text)  # Context for translators
    is_html = Column(Boolean, default=False)  # Whether value contains HTML
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "key", "language_code", "namespace", name="uix_translation_key_lang_ns"
        ),
    )


class ContentTranslation(Base):
    """
    Stores translations for dynamic content (courses, lessons, etc.).
    Polymorphic model that can translate any content type.
    """

    __tablename__ = "content_translations"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(
        String(50), nullable=False, index=True
    )  # e.g., 'course', 'lesson', 'quiz'
    content_id = Column(
        Integer, nullable=False, index=True
    )  # ID of the content being translated
    field_name = Column(
        String(100), nullable=False
    )  # Field being translated (title, description, etc.)
    language_code = Column(String(10), nullable=False, index=True)
    translated_value = Column(Text, nullable=False)
    is_machine_translated = Column(
        Boolean, default=False
    )  # Whether AI-translated or human
    translator_notes = Column(Text)  # Notes for translators or context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "content_type",
            "content_id",
            "field_name",
            "language_code",
            name="uix_content_translation",
        ),
    )


class UserLanguagePreference(Base):
    """
    User language preferences.
    Stores per-user language settings.
    """

    __tablename__ = "user_language_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    preferred_language = Column(
        String(10), default="en", nullable=False
    )  # User's preferred UI language
    content_languages = Column(
        String(255)
    )  # Comma-separated list of acceptable content languages
    auto_translate = Column(Boolean, default=True)  # Automatically translate content
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
