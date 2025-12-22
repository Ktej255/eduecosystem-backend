import pyotp
import qrcode
import io
import base64
import os
import secrets
from typing import List
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from app.models.two_factor import TwoFactorAuth, TwoFactorBackupCode
from datetime import datetime


class TwoFactorService:
    def __init__(self):
        # Ensure encryption key exists or generate one for dev (WARNING: Persist this in prod!)
        key = os.getenv("TWO_FACTOR_ENCRYPTION_KEY")
        if not key:
            # For development safety, we'll log a warning but generate a temporary one
            # In production, this should raise an error
            print("WARNING: TWO_FACTOR_ENCRYPTION_KEY not set. Using temporary key.")
            key = Fernet.generate_key().decode()
        self.cipher_suite = Fernet(key.encode() if isinstance(key, str) else key)
        self.issuer_name = "Eduecosystem"

    def _encrypt_secret(self, secret: str) -> str:
        return self.cipher_suite.encrypt(secret.encode()).decode()

    def _decrypt_secret(self, encrypted_secret: str) -> str:
        return self.cipher_suite.decrypt(encrypted_secret.encode()).decode()

    def generate_totp_secret(self) -> str:
        """Generate a new random TOTP secret."""
        return pyotp.random_base32()

    def get_totp_uri(self, user_email: str, secret: str) -> str:
        """Generate the provisioning URI for the authenticator app."""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email, issuer_name=self.issuer_name
        )

    def generate_qr_code(self, uri: str) -> str:
        """Generate a base64 encoded QR code image from the URI."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify a TOTP code against a secret."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate a list of random backup codes."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def enable_2fa(self, db: Session, user_id: int, secret: str, code: str) -> bool:
        """
        Verify the code and enable 2FA for the user.
        Saves the encrypted secret and generates backup codes.
        """
        if not self.verify_totp(secret, code):
            return False

        # Create or Update TwoFactorAuth record
        encrypted_secret = self._encrypt_secret(secret)

        two_factor_auth = (
            db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        )

        if two_factor_auth:
            two_factor_auth.secret = encrypted_secret
            two_factor_auth.is_enabled = True
            two_factor_auth.verified_at = datetime.utcnow()
            # Clear old backup codes if any
            db.query(TwoFactorBackupCode).filter(
                TwoFactorBackupCode.user_id == user_id
            ).delete()
        else:
            two_factor_auth = TwoFactorAuth(
                user_id=user_id,
                secret=encrypted_secret,
                is_enabled=True,
                verified_at=datetime.utcnow(),
            )
            db.add(two_factor_auth)

        db.flush()  # Get ID for backup codes

        backup_codes = self.generate_backup_codes()
        for code_val in backup_codes:
            # Store encrypted code in code_hash field
            db_code = TwoFactorBackupCode(
                user_id=user_id,
                two_factor_auth_id=two_factor_auth.id,
                code_hash=self._encrypt_secret(code_val),
                is_used=False,
            )
            db.add(db_code)

        # User flag is a property based on relationship, so no need to update user table directly
        # unless we want to invalidate cache or something. But here it's a computed property.

        db.commit()
        return True

    def disable_2fa(self, db: Session, user_id: int) -> None:
        """Disable 2FA for a user."""
        # Remove 2FA record
        db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).delete()
        # Remove backup codes
        db.query(TwoFactorBackupCode).filter(
            TwoFactorBackupCode.user_id == user_id
        ).delete()

        # User flag is computed, no need to update

        db.commit()

    def validate_login(self, db: Session, user_id: int, code: str) -> bool:
        """
        Validate a 2FA code (TOTP or backup code) during login.
        """
        two_factor = (
            db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        )
        if not two_factor or not two_factor.is_enabled:
            return True  # 2FA not enabled, so validation passes (or should be handled by caller)

        # 1. Try TOTP
        try:
            secret = self._decrypt_secret(two_factor.secret)
            if self.verify_totp(secret, code):
                return True
        except Exception as e:
            print(f"Error validating TOTP: {e}")

        # 2. Try Backup Codes
        # We need to check all unused backup codes.
        # Since they are encrypted, we might need to decrypt them to compare,
        # or encrypt the input code? No, encryption is randomized (IV).
        # So we must iterate and decrypt. This is slightly inefficient but safe for 10 codes.
        backup_codes = (
            db.query(TwoFactorBackupCode)
            .filter(
                TwoFactorBackupCode.user_id == user_id,
                TwoFactorBackupCode.is_used == False,
            )
            .all()
        )

        for backup in backup_codes:
            try:
                decrypted_code = self._decrypt_secret(backup.code_hash)
                if decrypted_code == code:
                    # Mark as used
                    backup.is_used = True
                    db.commit()
                    return True
            except Exception:
                continue

        return False

    def get_backup_codes(self, db: Session, user_id: int) -> List[str]:
        """
        Retrieve valid backup codes for the user (e.g., to show them after setup).
        WARNING: Only call this immediately after generation/setup.
        """
        backup_codes = (
            db.query(TwoFactorBackupCode)
            .filter(
                TwoFactorBackupCode.user_id == user_id,
                TwoFactorBackupCode.is_used == False,
            )
            .all()
        )

        return [self._decrypt_secret(code.code_hash) for code in backup_codes]


two_factor_service = TwoFactorService()
