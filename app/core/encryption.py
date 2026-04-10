import base64
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_encryption_key() -> bytes:
    """Get a consistent encryption key derived from SECRET_KEY."""
    # We use SHA-256 to derive a 32-byte key from the SECRET_KEY
    try:
        from app.core.config import settings
        secret = settings.SECRET_KEY
    except ImportError:
        secret = "default_dev_secret_key"

    if not secret:
        # Fallback for dev if SECRET_KEY is not set
        secret = "default_dev_secret_key"

    # Needs to be a string before encoding
    if not isinstance(secret, str):
        secret = str(secret)

    return hashlib.sha256(secret.encode('utf-8')).digest()

def encrypt_string(plaintext: str) -> Optional[str]:
    """Encrypt a string and return base64 encoded ciphertext."""
    if not plaintext:
        return plaintext

    try:
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(get_encryption_key())
        f = Fernet(key)
        encrypted_bytes = f.encrypt(plaintext.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    except ImportError:
        logger.warning("cryptography package not available. Using unencrypted value.")
        return plaintext
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        return plaintext

def decrypt_string(ciphertext: str) -> Optional[str]:
    """Decrypt a base64 encoded ciphertext string."""
    if not ciphertext:
        return ciphertext

    try:
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(get_encryption_key())
        f = Fernet(key)

        # In case the string isn't encrypted, try to decrypt,
        # if it fails, return the original string assuming it's plaintext
        try:
            decoded_b64 = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = f.decrypt(decoded_b64)
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # If it's not a valid fernet token, return as is (for backwards compatibility)
            return ciphertext
    except ImportError:
        logger.warning("cryptography package not available. Assuming unencrypted value.")
        return ciphertext
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        return ciphertext
