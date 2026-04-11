"""
Storage abstraction layer for file uploads.

Supports local filesystem storage (development) and Google Cloud Storage (production).
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import google-cloud-storage for GCP support
try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound, Forbidden

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logger.warning("google-cloud-storage not installed. GCP storage unavailable.")


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file.

        Args:
            file_content: File bytes
            filename: Destination filename
            content_type: MIME type

        Returns:
            Tuple of (success, file_url, error_message)
        """
        pass

    @abstractmethod
    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file.

        Args:
            filename: File to delete

        Returns:
            Tuple of (success, error_message)
        """
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Check if file exists"""
        pass

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Get public URL for file"""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage (for development)"""

    def __init__(self, base_dir: str = "uploads"):
        """
        Initialize local storage.

        Args:
            base_dir: Base directory for uploads
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # Create subdirectories
        for subdir in ["videos", "images", "files"]:
            (self.base_dir / subdir).mkdir(exist_ok=True)

        logger.info(f"Local storage initialized at {self.base_dir.absolute()}")

    def upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload file to local filesystem"""
        try:
            # Determine subdirectory based on content type
            if content_type.startswith("image/"):
                subdir = "images"
            elif content_type.startswith("video/"):
                subdir = "videos"
            else:
                subdir = "files"

            file_path = self.base_dir / subdir / filename

            # Write file
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Return relative URL
            file_url = f"/uploads/{subdir}/{filename}"
            logger.info(f"File uploaded to local storage: {file_url}")

            return True, file_url, None

        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            return False, None, str(e)

    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Delete file from local filesystem"""
        try:
            # Try each subdirectory
            for subdir in ["videos", "images", "files"]:
                file_path = self.base_dir / subdir / filename
                if file_path.exists():
                    os.remove(file_path)
                    logger.info(f"File deleted from local storage: {filename}")
                    return True, None

            return False, "File not found"

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False, str(e)

    def exists(self, filename: str) -> bool:
        """Check if file exists in any subdirectory"""
        for subdir in ["videos", "images", "files"]:
            if (self.base_dir / subdir / filename).exists():
                return True
        return False

    def get_url(self, filename: str) -> str:
        """Get URL for file"""
        # Try to find in subdirectories
        for subdir in ["videos", "images", "files"]:
            if (self.base_dir / subdir / filename).exists():
                return f"/uploads/{subdir}/{filename}"
        return f"/uploads/files/{filename}"


class GCPStorage(StorageBackend):
    """Google Cloud Storage (for production)"""

    def __init__(
        self,
        bucket_name: str,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize GCP storage.

        Args:
            bucket_name: GCP bucket name
            credentials_path: Path to GCP service account JSON (uses environment GOOGLE_APPLICATION_CREDENTIALS if not provided)
        """
        if not GCP_AVAILABLE:
            raise ImportError(
                "google-cloud-storage is required for GCP storage. Install with: pip install google-cloud-storage"
            )

        self.bucket_name = bucket_name

        # Initialize GCP client
        try:
            if credentials_path:
                self.client = storage.Client.from_service_account_json(credentials_path)
            else:
                # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable natively
                self.client = storage.Client()

            self.bucket = self.client.bucket(bucket_name)
            # Verify bucket exists and is accessible
            if not self.bucket.exists():
                raise ValueError(f"GCP bucket '{bucket_name}' not found")

            logger.info(f"GCP storage initialized: gs://{bucket_name}")

        except Forbidden:
            raise ValueError(f"Access denied to GCP bucket '{bucket_name}'")
        except Exception as e:
            raise ValueError(f"GCP initialization error: {e}")

    def upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload file to GCP"""
        try:
            # Determine GCP path based on content type
            if content_type.startswith("image/"):
                gcp_path = f"images/{filename}"
            elif content_type.startswith("video/"):
                gcp_path = f"videos/{filename}"
            else:
                gcp_path = f"files/{filename}"

            blob = self.bucket.blob(gcp_path)
            blob.upload_from_string(file_content, content_type=content_type)

            # file_url = blob.public_url # Or custom domain

            file_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcp_path}"
            logger.info(f"File uploaded to GCP: {file_url}")

            return True, file_url, None

        except Exception as e:
            logger.error(f"Failed to upload file to GCP: {e}")
            return False, None, str(e)

    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Delete file from GCP"""
        try:
            for prefix in ["images/", "videos/", "files/"]:
                gcp_path = f"{prefix}{filename}"
                blob = self.bucket.blob(gcp_path)

                if blob.exists():
                    blob.delete()
                    logger.info(f"File deleted from GCP: {gcp_path}")
                    return True, None

            return False, "File not found"

        except Exception as e:
            logger.error(f"Failed to delete file from GCP: {e}")
            return False, str(e)

    def exists(self, filename: str) -> bool:
        """Check if file exists in GCP"""
        for prefix in ["images/", "videos/", "files/"]:
            gcp_path = f"{prefix}{filename}"
            blob = self.bucket.blob(gcp_path)
            if blob.exists():
                return True
        return False

    def get_url(self, filename: str) -> str:
        """Get public URL for file"""
        for prefix in ["images/", "videos/", "files/"]:
            gcp_path = f"{prefix}{filename}"
            if self.bucket.blob(gcp_path).exists():
                return f"https://storage.googleapis.com/{self.bucket_name}/{gcp_path}"

        # Default to files prefix
        return f"https://storage.googleapis.com/{self.bucket_name}/files/{filename}"

    def get_presigned_url(self, filename: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for secure file access.
        """
        for prefix in ["images/", "videos/", "files/"]:
            gcp_path = f"{prefix}{filename}"
            blob = self.bucket.blob(gcp_path)

            if blob.exists():
                import datetime
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=datetime.timedelta(seconds=expiration),
                    method="GET",
                )
                return url

        return None


# Global storage instance
_storage: Optional[StorageBackend] = None


def init_storage(backend: str = "local", **kwargs) -> StorageBackend:
    """
    Initialize the global storage backend.

    Args:
        backend: Storage backend type ('local' or 'gcp')
        **kwargs: Backend-specific configuration

    Returns:
        StorageBackend instance
    """
    global _storage

    if backend == "local":
        _storage = LocalStorage(**kwargs)
    elif backend == "gcp":
        _storage = GCPStorage(**kwargs)
    elif backend == "s3":
        logger.warning("S3 backend specified but we migrated to GCP. Falling back to GCP.")
        _storage = GCPStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage backend: {backend}")

    return _storage


def get_storage() -> StorageBackend:
    """
    Get the global storage backend instance.

    Returns:
        StorageBackend instance (creates local storage if not initialized)
    """
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage
