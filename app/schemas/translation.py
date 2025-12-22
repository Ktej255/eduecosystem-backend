"""
Translation Schemas

Pydantic schemas for translation API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime


# Language Schemas
class LanguageBase(BaseModel):
    code: str = Field(
        ..., min_length=2, max_length=10, description="Language code (ISO 639-1)"
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Language name in English"
    )
    native_name: str = Field(
        ..., min_length=1, max_length=100, description="Language name in native script"
    )
    is_rtl: bool = Field(default=False, description="Right-to-left language")
    is_active: bool = Field(default=True, description="Active language")
    flag_emoji: Optional[str] = Field(None, max_length=10, description="Flag emoji")
    sort_order: int = Field(default=0, description="Display order")


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    native_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_rtl: Optional[bool] = None
    is_active: Optional[bool] = None
    flag_emoji: Optional[str] = Field(None, max_length=10)
    sort_order: Optional[int] = None


class Language(LanguageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Translation Schemas
class TranslationBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=255, description="Translation key")
    language_code: str = Field(
        ..., min_length=2, max_length=10, description="Language code"
    )
    value: str = Field(..., min_length=1, description="Translated text")
    namespace: str = Field(
        default="common", max_length=100, description="Translation namespace"
    )
    description: Optional[str] = Field(None, description="Context for translators")
    is_html: bool = Field(default=False, description="Contains HTML")


class TranslationCreate(TranslationBase):
    pass


class TranslationUpdate(BaseModel):
    value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_html: Optional[bool] = None


class Translation(TranslationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TranslationBulkCreate(BaseModel):
    """Bulk create translations for a single language"""

    language_code: str = Field(..., min_length=2, max_length=10)
    namespace: str = Field(default="common", max_length=100)
    translations: Dict[str, str] = Field(..., description="Map of key -> value")


class TranslationExport(BaseModel):
    """Export translations for a language"""

    language_code: str
    namespace: str
    translations: Dict[str, str]
    total_count: int


# Content Translation Schemas
class ContentTranslationBase(BaseModel):
    content_type: str = Field(
        ..., max_length=50, description="Type of content (course, lesson, etc.)"
    )
    content_id: int = Field(..., description="ID of content to translate")
    field_name: str = Field(
        ..., max_length=100, description="Field name (title, description, etc.)"
    )
    language_code: str = Field(..., min_length=2, max_length=10)
    translated_value: str = Field(..., min_length=1)
    is_machine_translated: bool = Field(default=False)
    translator_notes: Optional[str] = None


class ContentTranslationCreate(ContentTranslationBase):
    pass


class ContentTranslationUpdate(BaseModel):
    translated_value: Optional[str] = Field(None, min_length=1)
    is_machine_translated: Optional[bool] = None
    translator_notes: Optional[str] = None


class ContentTranslation(ContentTranslationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ContentTranslationRequest(BaseModel):
    """Request to translate content"""

    content_type: str
    content_id: int
    target_languages: List[str] = Field(
        ..., description="List of language codes to translate to"
    )
    fields: List[str] = Field(
        default=["title", "description"], description="Fields to translate"
    )
    use_ai: bool = Field(default=True, description="Use AI translation")


class TranslateTextRequest(BaseModel):
    """Request to translate arbitrary text"""

    text: str = Field(..., min_length=1, max_length=10000)
    source_language: str = Field(..., min_length=2, max_length=10)
    target_language: str = Field(..., min_length=2, max_length=10)
    preserve_html: bool = Field(default=False, description="Preserve HTML tags")


class TranslateTextResponse(BaseModel):
    """Response for text translation"""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    is_machine_translated: bool = True


# User Language Preference Schemas
class UserLanguagePreferenceBase(BaseModel):
    preferred_language: str = Field(default="en", min_length=2, max_length=10)
    content_languages: Optional[str] = Field(
        None, description="Comma-separated language codes"
    )
    auto_translate: bool = Field(default=True)


class UserLanguagePreferenceCreate(UserLanguagePreferenceBase):
    user_id: int


class UserLanguagePreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = Field(None, min_length=2, max_length=10)
    content_languages: Optional[str] = None
    auto_translate: Optional[bool] = None


class UserLanguagePreference(UserLanguagePreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Localization Info
class LocalizationInfo(BaseModel):
    """Information about current localization state"""

    available_languages: List[Language]
    current_language: str
    user_preference: Optional[UserLanguagePreference]
    rtl_enabled: bool
    namespaces: List[str] = Field(
        default=["common", "auth", "course", "quiz", "discussion"]
    )


# Translation Statistics
class TranslationStats(BaseModel):
    """Statistics about translation coverage"""

    language_code: str
    language_name: str
    total_keys: int
    translated_keys: int
    untranslated_keys: int
    completion_percentage: float
    namespaces: Dict[
        str, Dict[str, int]
    ]  # namespace -> {total, translated, untranslated}


class TranslationCoverageReport(BaseModel):
    """Overall translation coverage report"""

    languages: List[TranslationStats]
    total_languages: int
    base_language: str = "en"
    generated_at: datetime
