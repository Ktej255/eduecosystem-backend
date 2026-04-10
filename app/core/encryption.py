import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

def _derive_fernet_key(raw_key: str) -> bytes:
    """Derive a valid 32-byte url-safe base64 Fernet key from any string."""
    digest = hashlib.sha256(raw_key.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def get_encryption_key() -> str:
    key = getattr(settings, "SSO_ENCRYPTION_KEY", "")
    if not key:
        env = getattr(settings, "ENVIRONMENT", "development")
        if env == "production":
            raise ValueError("CRITICAL: SSO_ENCRYPTION_KEY must be set in production")
        else:
            logger.warning("WARNING: SSO_ENCRYPTION_KEY not set. Using deterministic fallback key derived from SECRET_KEY.")
            key = getattr(settings, "SECRET_KEY", "fallback_secret")

    return _derive_fernet_key(key).decode()

_cipher_suite = None

def get_cipher_suite():
    global _cipher_suite
    if _cipher_suite is None:
        key = get_encryption_key()
        _cipher_suite = Fernet(key.encode() if isinstance(key, str) else key)
    return _cipher_suite

def encrypt_secret(secret: str) -> str:
    """Encrypt a secret string for safe storage in the database."""
    if not secret:
        return secret
    return get_cipher_suite().encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret: str) -> str:
    """Decrypt a secret string from the database."""
    if not encrypted_secret:
        return encrypted_secret
    try:
        return get_cipher_suite().decrypt(encrypted_secret.encode()).decode()
    except Exception:
        logger.warning("Failed to decrypt secret, assuming it is a legacy plaintext value.")
        return encrypted_secret
