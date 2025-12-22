"""
Translation API Endpoints

RESTful API for translation management and localization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.translation import Language, Translation
from app.schemas.translation import (
    Language as LanguageSchema,
    LanguageCreate,
    LanguageUpdate,
    Translation as TranslationSchema,
    TranslationCreate,
    TranslationUpdate,
    TranslationBulkCreate,
    TranslationExport,
    ContentTranslationRequest,
    TranslateTextRequest,
    TranslateTextResponse,
    UserLanguagePreference as UserLanguagePreferenceSchema,
    UserLanguagePreferenceUpdate,
    LocalizationInfo,
    TranslationStats,
    TranslationCoverageReport,
)
from app.services.translation_service import (
    TranslationService,
    ContentTranslationService,
    UserLanguageService,
)
from app.services.ai_translation_service import translate_text_ai, LANGUAGE_METADATA
from app.middleware.i18n_middleware import get_request_language
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Language Management ====================


@router.get("/languages", response_model=List[LanguageSchema])
def get_languages(
    active_only: bool = Query(True, description="Only return active languages"),
    db: Session = Depends(get_db),
):
    """Get all supported languages."""
    query = db.query(Language)

    if active_only:
        query = query.filter(Language.is_active == True)

    languages = query.order_by(Language.sort_order, Language.name).all()
    return languages


@router.post(
    "/languages", response_model=LanguageSchema, status_code=status.HTTP_201_CREATED
)
def create_language(
    language: LanguageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user),
):
    """Create a new language (Admin only)."""
    # Check if language already exists
    existing = db.query(Language).filter(Language.code == language.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Language already exists"
        )

    db_language = Language(**language.dict())
    db.add(db_language)
    db.commit()
    db.refresh(db_language)

    logger.info(f"Language created: {language.code} by user {current_user.id}")
    return db_language


@router.patch("/languages/{language_id}", response_model=LanguageSchema)
def update_language(
    language_id: int,
    language_update: LanguageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user),
):
    """Update a language (Admin only)."""
    db_language = db.query(Language).filter(Language.id == language_id).first()
    if not db_language:
        raise HTTPException(status_code=404, detail="Language not found")

    for key, value in language_update.dict(exclude_unset=True).items():
        setattr(db_language, key, value)

    db.commit()
    db.refresh(db_language)
    return db_language


# ==================== UI Translations ====================


@router.get("/translations/{namespace}", response_model=TranslationExport)
def get_translations(
    namespace: str = "common",
    language: str = Query(
        None, description="Language code (default: request language)"
    ),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get all translations for a namespace and language."""
    lang_code = language or get_request_language(request)

    translations = TranslationService.get_translations_by_namespace(
        db, lang_code, namespace
    )

    return TranslationExport(
        language_code=lang_code,
        namespace=namespace,
        translations=translations,
        total_count=len(translations),
    )


@router.post(
    "/translations",
    response_model=TranslationSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_translation(
    translation: TranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user),
):
    """Create a new translation (Admin only)."""
    return TranslationService.create_translation(db, translation)


@router.patch("/translations/{translation_id}", response_model=TranslationSchema)
def update_translation(
    translation_id: int,
    translation_update: TranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user),
):
    """Update a translation (Admin only)."""
    updated = TranslationService.update_translation(
        db, translation_id, translation_update
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Translation not found")
    return updated


@router.post("/translations/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_translations(
    bulk_data: TranslationBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user),
):
    """Bulk create/update translations (Admin only)."""
    count = TranslationService.bulk_create_translations(
        db, bulk_data.language_code, bulk_data.namespace, bulk_data.translations
    )

    return {
        "message": f"Created/updated {count} translations",
        "language_code": bulk_data.language_code,
        "namespace": bulk_data.namespace,
        "count": count,
    }


# ==================== Content Translation ====================


@router.post("/content/translate", response_model=Dict[str, Any])
async def translate_content(
    request_data: ContentTranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Translate dynamic content using AI."""
    # Verify user has access to the content
    # (Add authorization logic based on content_type)

    try:
        results = await ContentTranslationService.translate_content_ai(
            db=db,
            content_type=request_data.content_type,
            content_id=request_data.content_id,
            source_language="en",  # Assume English source
            target_languages=request_data.target_languages,
            fields=request_data.fields,
        )

        return results

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Content translation error: {e}")
        raise HTTPException(
            status_code=500, detail="Translation failed. Please try again."
        )


@router.post("/translate-text", response_model=TranslateTextResponse)
async def translate_text(
    request_data: TranslateTextRequest,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Translate arbitrary text using AI."""
    try:
        translated_text = await translate_text_ai(
            text=request_data.text,
            source_language=request_data.source_language,
            target_language=request_data.target_language,
            preserve_html=request_data.preserve_html,
        )

        return TranslateTextResponse(
            original_text=request_data.text,
            translated_text=translated_text,
            source_language=request_data.source_language,
            target_language=request_data.target_language,
            is_machine_translated=True,
        )

    except Exception as e:
        logger.error(f"Text translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# ==================== User Preferences ====================


@router.get("/preferences", response_model=UserLanguagePreferenceSchema)
def get_user_language_preferences(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current user's language preferences."""
    preference = UserLanguageService.get_user_preference(db, current_user.id)

    if not preference:
        # Return default preference
        return UserLanguagePreferenceSchema(
            id=0,
            user_id=current_user.id,
            preferred_language="en",
            content_languages="en",
            auto_translate=True,
            created_at=datetime.utcnow(),
            updated_at=None,
        )

    return preference


@router.patch("/preferences", response_model=UserLanguagePreferenceSchema)
def update_user_language_preferences(
    preferences: UserLanguagePreferenceUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update current user's language preferences."""
    updated_pref = UserLanguageService.set_user_preference(
        db,
        current_user.id,
        language_code=preferences.preferred_language or "en",
        content_languages=preferences.content_languages,
        auto_translate=preferences.auto_translate
        if preferences.auto_translate is not None
        else True,
    )

    logger.info(
        f"User {current_user.id} updated language preferences to {updated_pref.preferred_language}"
    )
    return updated_pref


# ==================== Localization Info ====================


@router.get("/info", response_model=LocalizationInfo)
def get_localization_info(
    request: Request,
    current_user: User = Depends(deps.get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Get localization information for the current request."""
    # Get available languages
    languages = (
        db.query(Language)
        .filter(Language.is_active == True)
        .order_by(Language.sort_order)
        .all()
    )

    # Get current language
    current_lang = get_request_language(request)

    # Get user preference if authenticated
    user_pref = None
    if current_user:
        user_pref = UserLanguageService.get_user_preference(db, current_user.id)

    # Check if RTL
    current_lang_obj = db.query(Language).filter(Language.code == current_lang).first()
    is_rtl = current_lang_obj.is_rtl if current_lang_obj else False

    return LocalizationInfo(
        available_languages=languages,
        current_language=current_lang,
        user_preference=user_pref,
        rtl_enabled=is_rtl,
    )


# ==================== Translation Statistics ====================


@router.get("/stats", response_model=TranslationCoverageReport)
def get_translation_stats(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_admin_user)
):
    """Get translation coverage statistics (Admin only)."""
    # Get all active languages
    languages = db.query(Language).filter(Language.is_active == True).all()

    # Get base language (English) translation count
    base_translations = (
        db.query(Translation).filter(Translation.language_code == "en").count()
    )

    stats_list = []

    for lang in languages:
        # Get translation count for this language
        lang_translations = (
            db.query(Translation).filter(Translation.language_code == lang.code).count()
        )

        # Calculate percentages
        completion = (
            (lang_translations / base_translations * 100)
            if base_translations > 0
            else 0
        )

        # Get namespace breakdown
        namespaces = {}
        for namespace in ["common", "auth", "course", "quiz", "discussion"]:
            total = (
                db.query(Translation)
                .filter(
                    Translation.language_code == "en",
                    Translation.namespace == namespace,
                )
                .count()
            )

            translated = (
                db.query(Translation)
                .filter(
                    Translation.language_code == lang.code,
                    Translation.namespace == namespace,
                )
                .count()
            )

            namespaces[namespace] = {
                "total": total,
                "translated": translated,
                "untranslated": total - translated,
            }

        stats_list.append(
            TranslationStats(
                language_code=lang.code,
                language_name=lang.name,
                total_keys=base_translations,
                translated_keys=lang_translations,
                untranslated_keys=base_translations - lang_translations,
                completion_percentage=round(completion, 2),
                namespaces=namespaces,
            )
        )

    return TranslationCoverageReport(
        languages=stats_list,
        total_languages=len(languages),
        base_language="en",
        generated_at=datetime.utcnow(),
    )


# ==================== Initialize Default Languages ====================


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
def initialize_languages(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_admin_user)
):
    """Initialize default languages from metadata (Admin only, run once)."""
    created_count = 0

    for code, metadata in LANGUAGE_METADATA.items():
        existing = db.query(Language).filter(Language.code == code).first()
        if not existing:
            lang = Language(
                code=code,
                name=metadata["name"],
                native_name=metadata["native_name"],
                is_rtl=metadata["rtl"],
                flag_emoji=metadata["flag"],
                is_active=True,
                sort_order=created_count,
            )
            db.add(lang)
            created_count += 1

    db.commit()

    logger.info(f"Initialized {created_count} languages")

    return {"message": f"Initialized {created_count} languages", "count": created_count}
