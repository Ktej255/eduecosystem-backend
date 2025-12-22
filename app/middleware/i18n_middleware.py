"""
i18n Middleware

Language detection and header processing middleware for internationalization.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class I18nMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and set user's preferred language.

    Language detection priority:
    1. Query parameter (?lang=es)
    2. User preference from database (if authenticated)
    3. Accept-Language header
    4. Default language (en)
    """

    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "ar", "hi", "zh"]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and detect language."""

        # Detect language
        language = await self._detect_language(request)

        # Store language in request state
        request.state.language = language
        request.state.is_rtl = language in ["ar", "he", "fa", "ur"]  # RTL languages

        # Process request
        response = await call_next(request)

        # Add language headers to response
        response.headers["Content-Language"] = language
        if request.state.is_rtl:
            response.headers["X-RTL-Enabled"] = "true"

        return response

    async def _detect_language(self, request: Request) -> str:
        """
        Detect user's preferred language.

        Args:
            request: FastAPI request object

        Returns:
            Language code (e.g., 'en', 'es')
        """
        # 1. Check query parameter
        lang_param = request.query_params.get("lang")
        if lang_param and lang_param in self.SUPPORTED_LANGUAGES:
            logger.debug(f"Language from query parameter: {lang_param}")
            return lang_param

        # 2. Check user preference (if authenticated)
        if hasattr(request.state, "user") and request.state.user:
            try:
                from app.db.session import SessionLocal
                from app.models.translation import UserLanguagePreference

                db = SessionLocal()
                user_pref = (
                    db.query(UserLanguagePreference)
                    .filter(UserLanguagePreference.user_id == request.state.user.id)
                    .first()
                )
                db.close()

                if (
                    user_pref
                    and user_pref.preferred_language in self.SUPPORTED_LANGUAGES
                ):
                    logger.debug(
                        f"Language from user preference: {user_pref.preferred_language}"
                    )
                    return user_pref.preferred_language
            except Exception as e:
                logger.warning(f"Error fetching user language preference: {e}")

        # 3. Check Accept-Language header
        accept_language = request.headers.get("Accept-Language")
        if accept_language:
            language = self._parse_accept_language(accept_language)
            if language:
                logger.debug(f"Language from Accept-Language header: {language}")
                return language

        # 4. Default language
        logger.debug(f"Using default language: {self.DEFAULT_LANGUAGE}")
        return self.DEFAULT_LANGUAGE

    def _parse_accept_language(self, accept_language: str) -> Optional[str]:
        """
        Parse Accept-Language header and return best match.

        Format: "en-US,en;q=0.9,es;q=0.8,fr;q=0.7"

        Args:
            accept_language: Accept-Language header value

        Returns:
            Language code or None
        """
        try:
            # Split by comma
            languages = accept_language.split(",")

            # Parse and sort by quality
            parsed = []
            for lang in languages:
                lang = lang.strip()
                if ";q=" in lang:
                    code, quality = lang.split(";q=")
                    quality = float(quality)
                else:
                    code = lang
                    quality = 1.0

                # Extract base language code (e.g., 'en' from 'en-US')
                base_code = code.split("-")[0].lower()

                if base_code in self.SUPPORTED_LANGUAGES:
                    parsed.append((base_code, quality))

            # Sort by quality (highest first)
            parsed.sort(key=lambda x: x[1], reverse=True)

            # Return highest quality language
            if parsed:
                return parsed[0][0]

        except Exception as e:
            logger.warning(f"Error parsing Accept-Language header: {e}")

        return None


def get_request_language(request: Request) -> str:
    """
    Helper function to get current request language.

    Args:
        request: FastAPI request object

    Returns:
        Language code
    """
    return getattr(request.state, "language", "en")


def is_rtl_language(request: Request) -> bool:
    """
    Check if current language is RTL.

    Args:
        request: FastAPI request object

    Returns:
        True if RTL language
    """
    return getattr(request.state, "is_rtl", False)
