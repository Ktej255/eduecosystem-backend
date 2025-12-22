"""
Translation Service

Business logic for translation management and AI-powered translation.
"""

from sqlalchemy.orm import Session
from app.models.translation import (
    Translation,
    ContentTranslation,
    UserLanguagePreference,
)
from app.schemas.translation import (
    TranslationCreate,
    TranslationUpdate,
    ContentTranslationCreate,
)
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for managing translations."""

    @staticmethod
    def get_translation(
        db: Session, key: str, language_code: str, namespace: str = "common"
    ) -> Optional[str]:
        """
        Get translation for a key.

        Args:
            db: Database session
            key: Translation key
            language_code: Language code
            namespace: Translation namespace

        Returns:
            Translated value or None
        """
        translation = (
            db.query(Translation)
            .filter(
                Translation.key == key,
                Translation.language_code == language_code,
                Translation.namespace == namespace,
            )
            .first()
        )

        return translation.value if translation else None

    @staticmethod
    def get_translations_by_namespace(
        db: Session, language_code: str, namespace: str = "common"
    ) -> Dict[str, str]:
        """
        Get all translations for a namespace.

        Args:
            db: Database session
            language_code: Language code
            namespace: Translation namespace

        Returns:
            Dictionary of key -> value
        """
        translations = (
            db.query(Translation)
            .filter(
                Translation.language_code == language_code,
                Translation.namespace == namespace,
            )
            .all()
        )

        return {t.key: t.value for t in translations}

    @staticmethod
    def create_translation(db: Session, translation: TranslationCreate) -> Translation:
        """
        Create a new translation.

        Args:
            db: Database session
            translation: Translation data

        Returns:
            Created translation
        """
        db_translation = Translation(**translation.dict())
        db.add(db_translation)
        db.commit()
        db.refresh(db_translation)
        return db_translation

    @staticmethod
    def update_translation(
        db: Session, translation_id: int, update_data: TranslationUpdate
    ) -> Optional[Translation]:
        """
        Update a translation.

        Args:
            db: Database session
            translation_id: Translation ID
            update_data: Update data

        Returns:
            Updated translation or None
        """
        translation = (
            db.query(Translation).filter(Translation.id == translation_id).first()
        )
        if not translation:
            return None

        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(translation, key, value)

        db.commit()
        db.refresh(translation)
        return translation

    @staticmethod
    def bulk_create_translations(
        db: Session, language_code: str, namespace: str, translations: Dict[str, str]
    ) -> int:
        """
        Bulk create translations.

        Args:
            db: Database session
            language_code: Language code
            namespace: Translation namespace
            translations: Dictionary of key -> value

        Returns:
            Number of translations created
        """
        count = 0
        for key, value in translations.items():
            # Check if translation already exists
            existing = (
                db.query(Translation)
                .filter(
                    Translation.key == key,
                    Translation.language_code == language_code,
                    Translation.namespace == namespace,
                )
                .first()
            )

            if existing:
                # Update existing
                existing.value = value
            else:
                # Create new
                db_translation = Translation(
                    key=key,
                    language_code=language_code,
                    value=value,
                    namespace=namespace,
                )
                db.add(db_translation)
                count += 1

        db.commit()
        return count


class ContentTranslationService:
    """Service for translating dynamic content."""

    @staticmethod
    def get_content_translation(
        db: Session,
        content_type: str,
        content_id: int,
        field_name: str,
        language_code: str,
    ) -> Optional[str]:
        """
        Get translated content.

        Args:
            db: Database session
            content_type: Type of content
            content_id: Content ID
            field_name: Field name
            language_code: Language code

        Returns:
            Translated value or None
        """
        translation = (
            db.query(ContentTranslation)
            .filter(
                ContentTranslation.content_type == content_type,
                ContentTranslation.content_id == content_id,
                ContentTranslation.field_name == field_name,
                ContentTranslation.language_code == language_code,
            )
            .first()
        )

        return translation.translated_value if translation else None

    @staticmethod
    def create_content_translation(
        db: Session, translation: ContentTranslationCreate
    ) -> ContentTranslation:
        """
        Create content translation.

        Args:
            db: Database session
            translation: Translation data

        Returns:
            Created translation
        """
        db_translation = ContentTranslation(**translation.dict())
        db.add(db_translation)
        db.commit()
        db.refresh(db_translation)
        return db_translation

    @staticmethod
    async def translate_content_ai(
        db: Session,
        content_type: str,
        content_id: int,
        source_language: str,
        target_languages: List[str],
        fields: List[str],
    ) -> Dict[str, Any]:
        """
        Translate content using AI.

        Args:
            db: Database session
            content_type: Type of content (course, lesson, etc.)
            content_id: Content ID
            source_language: Source language code
            target_languages: List of target language codes
            fields: List of fields to translate

        Returns:
            Dictionary with translation results
        """
        from app.services.ai_translation_service import translate_text_ai

        # Get the content model
        content = ContentTranslationService._get_content_object(
            db, content_type, content_id
        )

        if not content:
            raise ValueError(f"Content not found: {content_type} {content_id}")

        results = {
            "content_type": content_type,
            "content_id": content_id,
            "translations": [],
        }

        for target_lang in target_languages:
            for field in fields:
                # Get source text
                source_text = getattr(content, field, None)
                if not source_text:
                    continue

                # Translate
                try:
                    translated_text = await translate_text_ai(
                        text=source_text,
                        source_language=source_language,
                        target_language=target_lang,
                    )

                    # Save translation
                    translation = ContentTranslationCreate(
                        content_type=content_type,
                        content_id=content_id,
                        field_name=field,
                        language_code=target_lang,
                        translated_value=translated_text,
                        is_machine_translated=True,
                    )

                    ContentTranslationService.create_content_translation(
                        db, translation
                    )

                    results["translations"].append(
                        {"field": field, "language": target_lang, "status": "success"}
                    )

                except Exception as e:
                    logger.error(
                        f"Translation failed for {field} to {target_lang}: {e}"
                    )
                    results["translations"].append(
                        {
                            "field": field,
                            "language": target_lang,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

        return results

    @staticmethod
    def _get_content_object(db: Session, content_type: str, content_id: int):
        """Get content object by type and ID."""
        from app.models.course import Course
        from app.models.lesson import Lesson
        from app.models.quiz import Quiz

        model_map = {"course": Course, "lesson": Lesson, "quiz": Quiz}

        model = model_map.get(content_type)
        if not model:
            return None

        return db.query(model).filter(model.id == content_id).first()


class UserLanguageService:
    """Service for managing user language preferences."""

    @staticmethod
    def get_user_preference(
        db: Session, user_id: int
    ) -> Optional[UserLanguagePreference]:
        """
        Get user's language preference.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User language preference or None
        """
        return (
            db.query(UserLanguagePreference)
            .filter(UserLanguagePreference.user_id == user_id)
            .first()
        )

    @staticmethod
    def set_user_preference(
        db: Session,
        user_id: int,
        language_code: str,
        content_languages: Optional[str] = None,
        auto_translate: bool = True,
    ) -> UserLanguagePreference:
        """
        Set user's language preference.

        Args:
            db: Database session
            user_id: User ID
            language_code: Preferred language code
            content_languages: Content language preferences
            auto_translate: Auto-translate content

        Returns:
            User language preference
        """
        preference = UserLanguageService.get_user_preference(db, user_id)

        if preference:
            # Update existing
            preference.preferred_language = language_code
            if content_languages is not None:
                preference.content_languages = content_languages
            preference.auto_translate = auto_translate
        else:
            # Create new
            preference = UserLanguagePreference(
                user_id=user_id,
                preferred_language=language_code,
                content_languages=content_languages,
                auto_translate=auto_translate,
            )
            db.add(preference)

        db.commit()
        db.refresh(preference)
        return preference
