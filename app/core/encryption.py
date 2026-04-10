import os
import base64
from cryptography.fernet import Fernet
from app.core.config import settings

def get_encryption_key() -> bytes:
    """
    Get the encryption key from settings or environment.
    Falls back to SECRET_KEY for convenience but ideally uses a dedicated key.
    """
    key_str = os.getenv("ENCRYPTION_KEY", "")
    if key_str:
        return key_str.encode()

    secret = settings.SECRET_KEY.encode()
    if len(secret) < 32:
        secret = secret.ljust(32, b'0')
    elif len(secret) > 32:
        secret = secret[:32]

    return base64.urlsafe_b64encode(secret)

def get_cipher() -> Fernet:
    """Get the Fernet cipher instance."""
    return Fernet(get_encryption_key())

from typing import Optional

def encrypt_string(text: Optional[str]) -> Optional[str]:
    """Encrypt a string and return the url-safe base64-encoded result."""
    if not text:
        return text
    cipher = get_cipher()
    return cipher.encrypt(text.encode()).decode()

def decrypt_string(encrypted_text: Optional[str]) -> Optional[str]:
    """Decrypt a url-safe base64-encoded string."""
    if not encrypted_text:
        return encrypted_text

    # Check if it's already encrypted (Fernet tokens usually start with 'gAAAAA')
    if not encrypted_text.startswith('gAAAAA'):
        # For smooth transition, if it's not encrypted, we just return it
        return encrypted_text

    cipher = get_cipher()
    try:
        return cipher.decrypt(encrypted_text.encode()).decode()
    except Exception:
        # If decryption fails, return original
        return encrypted_text
