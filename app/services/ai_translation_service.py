"""
AI Translation Service

AI-powered translation using OpenAI or other translation APIs.
"""

from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


async def translate_text_ai(
    text: str, source_language: str, target_language: str, preserve_html: bool = False
) -> str:
    """
    Translate text using AI (OpenAI GPT).

    Args:
        text: Text to translate
        source_language: Source language code
        target_language: Target language code
        preserve_html: Whether to preserve HTML tags

    Returns:
        Translated text

    Raises:
        Exception: If translation fails
    """
    try:
        # Check if OpenAI is available
        openai_key = os.getenv("OPENAI_API_KEY")

        if openai_key:
            return await _translate_with_openai(
                text, source_language, target_language, preserve_html
            )
        else:
            # Fallback to basic translation or error
            logger.warning("OpenAI API key not configured, translation unavailable")
            return text  # Return original text as fallback

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise


async def _translate_with_openai(
    text: str, source_language: str, target_language: str, preserve_html: bool
) -> str:
    """
    Translate using OpenAI GPT-4.

    Args:
        text: Text to translate
        source_language: Source language code
        target_language: Target language code
        preserve_html: Whether to preserve HTML tags

    Returns:
        Translated text
    """
    try:
        import openai

        # Language code to full name mapping
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ar": "Arabic",
            "hi": "Hindi",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "pt": "Portuguese",
            "ru": "Russian",
            "it": "Italian",
        }

        source_lang_name = language_names.get(source_language, source_language)
        target_lang_name = language_names.get(target_language, target_language)

        # Build prompt
        if preserve_html:
            prompt = f"""Translate the following text from {source_lang_name} to {target_lang_name}.
IMPORTANT: Preserve all HTML tags exactly as they are. Only translate the text content, not the HTML tags or attributes.

Text to translate:
{text}

Translated text:"""
        else:
            prompt = f"""Translate the following text from {source_lang_name} to {target_lang_name}.
Maintain the same tone and style. Be accurate and natural.

Text to translate:
{text}

Translated text:"""

        # Call OpenAI API
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # or gpt-3.5-turbo for cost savings
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Provide accurate, natural translations while maintaining the original meaning and tone.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent translations
            max_tokens=2000,
        )

        translated_text = response.choices[0].message.content.strip()

        logger.info(
            f"Translated {len(text)} chars from {source_language} to {target_language}"
        )

        return translated_text

    except Exception as e:
        logger.error(f"OpenAI translation error: {e}")
        raise Exception(f"Translation failed: {str(e)}")


async def batch_translate(
    texts: list[str], source_language: str, target_language: str
) -> list[str]:
    """
    Batch translate multiple texts.

    Args:
        texts: List of texts to translate
        source_language: Source language code
        target_language: Target language code

    Returns:
        List of translated texts
    """
    translated = []

    for text in texts:
        try:
            result = await translate_text_ai(text, source_language, target_language)
            translated.append(result)
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            translated.append(text)  # Use original on failure

    return translated


def detect_language(text: str) -> Optional[str]:
    """
    Detect language of text.

    Args:
        text: Text to analyze

    Returns:
        Language code or None
    """
    try:
        # Simple heuristic-based detection
        # In production, use a proper language detection library like langdetect

        # Check for common patterns
        if any(ord(char) > 0x4E00 and ord(char) < 0x9FFF for char in text):
            return "zh"  # Chinese characters

        if any(ord(char) > 0x0600 and ord(char) < 0x06FF for char in text):
            return "ar"  # Arabic

        if any(ord(char) > 0x0900 and ord(char) < 0x097F for char in text):
            return "hi"  # Hindi (Devanagari)

        # For Latin-based languages, would need more sophisticated detection
        # For now, default to English
        return "en"

    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return None


# Language metadata
LANGUAGE_METADATA = {
    "en": {"name": "English", "native_name": "English", "rtl": False, "flag": "🇺🇸"},
    "es": {"name": "Spanish", "native_name": "Español", "rtl": False, "flag": "🇪🇸"},
    "fr": {"name": "French", "native_name": "Français", "rtl": False, "flag": "🇫🇷"},
    "de": {"name": "German", "native_name": "Deutsch", "rtl": False, "flag": "🇩🇪"},
    "ar": {"name": "Arabic", "native_name": "العربية", "rtl": True, "flag": "🇸🇦"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "rtl": False, "flag": "🇮🇳"},
    "zh": {"name": "Chinese", "native_name": "中文", "rtl": False, "flag": "🇨🇳"},
    "ja": {"name": "Japanese", "native_name": "日本語", "rtl": False, "flag": "🇯🇵"},
    "ko": {"name": "Korean", "native_name": "한국어", "rtl": False, "flag": "🇰🇷"},
    "pt": {
        "name": "Portuguese",
        "native_name": "Português",
        "rtl": False,
        "flag": "🇵🇹",
    },
    "ru": {"name": "Russian", "native_name": "Русский", "rtl": False, "flag": "🇷🇺"},
    "it": {"name": "Italian", "native_name": "Italiano", "rtl": False, "flag": "🇮🇹"},
}
