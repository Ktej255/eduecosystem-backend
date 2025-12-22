"""
File content validation module for secure file uploads.

This module validates files based on their actual content (magic numbers/file signatures)
rather than just relying on file extensions or MIME types, which can be spoofed.
"""

from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# File signatures (magic numbers) for common file types
FILE_SIGNATURES = {
    # Images
    "image/jpeg": [
        bytes([0xFF, 0xD8, 0xFF]),  # JPEG
    ],
    "image/png": [
        bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),  # PNG
    ],
    "image/gif": [
        bytes([0x47, 0x49, 0x46, 0x38, 0x37, 0x61]),  # GIF87a
        bytes([0x47, 0x49, 0x46, 0x38, 0x39, 0x61]),  # GIF89a
    ],
    "image/webp": [
        bytes([0x52, 0x49, 0x46, 0x46]),  # RIFF (check WEBP at offset 8)
    ],
    # Documents
    "application/pdf": [
        bytes([0x25, 0x50, 0x44, 0x46]),  # %PDF
    ],
    # Videos
    "video/mp4": [
        bytes([0x00, 0x00, 0x00]),  # ftyp box (check at offset 4)
    ],
    "video/webm": [
        bytes([0x1A, 0x45, 0xDF, 0xA3]),  # EBML
    ],
    # Office Documents
    "application/msword": [
        bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]),  # DOC
    ],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        bytes([0x50, 0x4B, 0x03, 0x04]),  # DOCX (ZIP format)
    ],
}

# File extension to MIME type mapping
EXTENSION_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def get_file_type_from_content(file_content: bytes) -> Optional[str]:
    """
    Detect file type from file content using magic numbers.

    Args:
        file_content: First bytes of the file (at least 64 bytes recommended)

    Returns:
        MIME type string if detected, None otherwise
    """
    if not file_content or len(file_content) < 4:
        return None

    # Check each known signature
    for mime_type, signatures in FILE_SIGNATURES.items():
        for signature in signatures:
            if file_content.startswith(signature):
                # Special case for WebP - need to verify WEBP marker at offset 8
                if mime_type == "image/webp":
                    if len(file_content) >= 12 and file_content[8:12] == b"WEBP":
                        return mime_type
                    continue

                # Special case for MP4 - check ftyp marker
                if mime_type == "video/mp4":
                    if len(file_content) >= 12 and b"ftyp" in file_content[4:12]:
                        return mime_type
                    continue

                return mime_type

    return None


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Validate file extension against allowed list.

    Args:
        filename: Original filename
        allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])

    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename:
        return False

    ext = filename.lower()
    if "." in ext:
        ext = "." + ext.split(".")[-1]
    else:
        return False

    return ext in [e.lower() for e in allowed_extensions]


def validate_file_content(
    file_content: bytes, filename: str, allowed_types: list[str]
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Comprehensive file validation based on content and extension.

    Args:
        file_content: File bytes (first 64+ bytes sufficient for detection)
        filename: Original filename
        allowed_types: List of allowed MIME types

    Returns:
        Tuple of (is_valid, detected_mime_type, error_message)
    """
    # Get file extension
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    ext_with_dot = f".{ext}"

    # Get expected MIME type from extension
    expected_mime = EXTENSION_TO_MIME.get(ext_with_dot)

    # Detect actual file type from content
    detected_mime = get_file_type_from_content(file_content)

    # Validation rules

    # 1. Check if detected type is in allowed types
    if detected_mime and detected_mime not in allowed_types:
        return False, detected_mime, f"File type '{detected_mime}' not allowed"

    # 2. If we have both expected and detected, they should match
    if expected_mime and detected_mime and expected_mime != detected_mime:
        # Special case: JPEG can have jpg or jpeg extension
        if not (expected_mime == "image/jpeg" and detected_mime == "image/jpeg"):
            return (
                False,
                detected_mime,
                (
                    f"File extension '.{ext}' doesn't match actual file type '{detected_mime}'. "
                    f"Possible file type spoofing."
                ),
            )

    # 3. If we couldn't detect the type, be cautious
    if not detected_mime and expected_mime:
        # For text files, we can't easily detect from magic numbers
        if expected_mime == "text/plain":
            if ext_with_dot == ".txt":
                return True, "text/plain", None

        # For unknown types, reject to be safe
        logger.warning(f"Could not detect file type for: {filename}")
        return False, None, "Could not verify file type"

    # 4. Final check: is the detected type allowed?
    if detected_mime and detected_mime not in allowed_types:
        return False, detected_mime, f"File type '{detected_mime}' not allowed"

    return True, detected_mime, None


def validate_image_file(
    file_content: bytes, filename: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate image file content.

    Args:
        file_content: Image file bytes
        filename: Original filename

    Returns:
        Tuple of (is_valid, error_message)
    """
    allowed_image_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    is_valid, detected_type, error = validate_file_content(
        file_content, filename, allowed_image_types
    )
    return is_valid, error


def validate_video_file(
    file_content: bytes, filename: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate video file content.

    Args:
        file_content: Video file bytes
        filename: Original filename

    Returns:
        Tuple of (is_valid, error_message)
    """
    allowed_video_types = ["video/mp4", "video/webm"]
    is_valid, detected_type, error = validate_file_content(
        file_content, filename, allowed_video_types
    )
    return is_valid, error


def validate_document_file(
    file_content: bytes, filename: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate document file content.

    Args:
        file_content: Document file bytes
        filename: Original filename

    Returns:
        Tuple of (is_valid, error_message)
    """
    allowed_doc_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]
    is_valid, detected_type, error = validate_file_content(
        file_content, filename, allowed_doc_types
    )
    return is_valid, error
